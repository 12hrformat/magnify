"""Interactive CLI: the magnify wizard.

Flow:
  1. banner + target prompts (name / email / username / domain)
  2. menu loop: email lookup, username hunt, dork workshop, AI pivot
  3. "save to a file?" -> spinner -> markdown + json report
"""

from __future__ import annotations

import argparse
import sys
import time

from . import (__version__, checkers, dorks, emailintel, help_menu, llm,
               report, search, ui)
from .session import Session, Target
from .usernames import generate as gen_usernames


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="magnify",
        description="interactive OSINT orchestrator (authorized use only)")
    p.add_argument("--name", help="target full name")
    p.add_argument("--email", help="target email")
    p.add_argument("--username", help="known username/handle")
    p.add_argument("--domain", help="target domain")
    p.add_argument("--sweep", action="store_true",
                   help="non-interactive: run username sweep")
    p.add_argument("--dorks", action="store_true",
                   help="non-interactive: build default dork battery")
    p.add_argument("--save", metavar="BASEPATH",
                   help="non-interactive: save report to BASEPATH.md/.json")
    p.add_argument("--help-backends", action="store_true",
                   help="show how to connect search/AI/email backends")
    p.add_argument("--status", action="store_true",
                   help="show which backends are currently connected")
    p.add_argument("--threads", type=int, default=16)
    p.add_argument("--timeout", type=float, default=10.0)
    p.add_argument("--no-color", action="store_true")
    p.add_argument("--version", action="version",
                   version=f"magnify {__version__}")
    return p


def _collect_target(session: Session) -> None:
    ui.info("describe the target (press Enter to skip any field)")
    t = session.target
    t.name = ui.ask("full name", t.name)
    t.email = ui.ask("email", t.email)
    t.username = ui.ask("known username/handle", t.username)
    t.domain = ui.ask("domain", t.domain)
    if t.empty():
        ui.warn("nothing set — fill something before running modules")


def _do_email_lookup(session: Session) -> None:
    email = session.target.email or ui.ask("email to look up")
    if not email:
        ui.err("no email given")
        return
    session.target.email = email
    with ui.spinner(f"querying DNS and services for {email}"):
        session.email_intel = emailintel.lookup(email)
    for line in emailintel.summarize(session.email_intel):
        ui.finding(line)


def _do_username_hunt(session: Session, threads: int, timeout: float) -> None:
    base = (session.target.username or
            (session.target.name and session.target.name.split()[0]) or "")
    if not base and session.target.name:
        base = session.target.name.split()[0]
    if not session.target.name and not session.target.username:
        base = ui.ask("name or handle to expand")
    if not base:
        ui.err("nothing to hunt")
        return
    name = session.target.name or base
    variants = gen_usernames(name)
    if session.target.username and session.target.username not in variants:
        variants.insert(0, session.target.username)
    session.usernames_checked = variants
    total = len(variants) * len(checkers.SITES)
    ui.info(f"{len(variants)} username variants × "
            f"{len(checkers.SITES)} sites = {total} probes")

    bar = ui.ProgressBar(total, label="sweeping")

    def _on_result(result: dict) -> None:
        note = ""
        if result["state"] == "found":
            note = f"+ {result['username']} @ {result['site']}"
        bar.update(1, note=note, hit=result["state"] == "found")

    hits = checkers.sweep(
        variants, threads=threads, timeout=timeout, on_result=_on_result)
    bar.finish()
    session.username_hits = hits
    ui.ok(f"sweep done — {len(hits)} hits")
    for hit in hits:
        tag = "" if hit["reliable"] else ui.dim(" [heuristic]")
        ui.finding(f"{hit['username']} @ {hit['site']} "
                   f"({hit['evidence']}){tag}  {hit['url']}")


def _do_dork_workshop(session: Session) -> None:
    if session.target.empty():
        ui.warn("no target set — dorks will be generic")
    config = dorks.DorkConfig()
    print(ui.bold("\n  file types (leak hunting)"))
    config.filetypes = [
        dorks.FILETYPES[i]
        for i in ui.select_table("filetype", dorks.FILETYPES, columns=4,
                                 default="none")]
    print(ui.bold("\n  sites"))
    labels = [label for label, _ in dorks.SITE_TABLE]
    config.sites = [labels[i] for i in ui.select_table(
        "site", labels, columns=3, default="none")]
    mod_labels = [label for label, _ in dorks.MODIFIERS]
    chosen = ui.select_table("modifiers", mod_labels, columns=2, default="none")
    config.modifiers = [mod_labels[i] for i in chosen]
    config.include_leaks = bool(session.target.email)
    session.dorks = dorks.build(session.target, config)
    ui.ok(f"{len(session.dorks)} dorks generated")
    for dork in session.dorks:
        print(f"    {ui.cyan('>')} {dork}")
    if search.backend():
        if ui.confirm(f"execute against {search.backend()}?"):
            with ui.spinner("running dork battery"):
                session.search_results = search.run(session.dorks)
            total = sum(len(r.get("hits", [])) for r in session.search_results)
            ui.ok(f"{total} search results collected")
    else:
        ui.info("no search backend configured — press [h] in the main "
                "menu for connection instructions")


def _do_ai_pivot(session: Session) -> None:
    if not llm.enabled():
        ui.warn("AI disabled — press [h] in the main menu for connection "
                "instructions (or set MAGNIFY_LLM_URL)")
        return
    payload = {
        "target": vars(session.target),
        "email_intel": session.email_intel,
        "username_hits": session.username_hits,
        "dorks": session.dorks[:40],
    }
    with ui.spinner("asking the model for pivots"):
        session.ai_notes = llm.ask(payload)
    if session.ai_notes.get("error"):
        ui.err(session.ai_notes["error"])
        return
    ui.ok("AI notes:")
    print(f"    {session.ai_notes.get('summary', '')}")
    for pivot in session.ai_notes.get("pivots", []):
        ui.finding(pivot)


def _save_flow(session: Session, ask_first: bool = True) -> None:
    if ask_first and not ui.confirm("save to a file?", default=True):
        return
    stamp = time.strftime("%Y%m%d-%H%M%S")
    basepath = ui.ask("output path", f"magnify-report-{stamp}")
    if not basepath:
        return
    try:
        with ui.spinner("pulling everything together"):
            md_path, json_path = report.save(session, basepath)
    except OSError as exc:
        ui.err(f"could not save report: {exc}")
        return
    ui.ok(f"report saved:\n      {md_path}\n      {json_path}")


def _interactive(args: argparse.Namespace) -> int:
    session = Session()
    if args.name:
        session.target.name = args.name
    if args.email:
        session.target.email = args.email
    if args.username:
        session.target.username = args.username
    if args.domain:
        session.target.domain = args.domain

    ui.banner()
    _collect_target(session)
    items = [
        ("1", "email lookup"),
        ("2", "username hunt (name -> variants -> sweep)"),
        ("3", "dork workshop (interactive table)"),
        ("4", "AI pivot suggestions"),
        ("5", "save report"),
        ("6", "edit target"),
        ("h", "help / connect a backend"),
        ("q", "quit"),
    ]
    while True:
        header = session.target.display() or "no target set"
        choice = ui.menu(f"magnify v{__version__}  —  {header}", items)
        if choice == "1":
            _do_email_lookup(session)
        elif choice == "2":
            _do_username_hunt(session, args.threads, args.timeout)
        elif choice == "3":
            _do_dork_workshop(session)
        elif choice == "4":
            _do_ai_pivot(session)
        elif choice == "5":
            _save_flow(session)
        elif choice == "6":
            _collect_target(session)
        elif choice == "h":
            help_menu.menu()
        elif choice == "quit":
            # Quitting must always work. Offer to save, but if the
            # prompt can't be answered (EOF / Ctrl-D), just leave.
            if not session.target.empty():
                try:
                    if ui.confirm("save a report before quitting?",
                                  default=False):
                        _save_flow(session, ask_first=False)
                except (EOFError, KeyboardInterrupt):
                    print()
            ui.info("stay legal out there.")
            return 0


def _noninteractive(args: argparse.Namespace) -> int:
    if args.status:
        help_menu.show_status()
        return 0
    if args.help_backends:
        for title, body in (
            ("connect a search backend", help_menu.SEARX_GUIDE),
            ("connect an AI backend", help_menu.LLM_GUIDE),
            ("connect email backends", help_menu.EMAIL_GUIDE),
            ("authorized use only", help_menu.LEGAL),
        ):
            print(ui.cyan(f"=== {title} ==="))
            print(body)
        return 0
    session = Session(Target(
        name=args.name or "", email=args.email or "",
        username=args.username or "", domain=args.domain or ""))
    if session.target.empty():
        print("error: provide at least one of --name/--email/"
              "--username/--domain", file=sys.stderr)
        return 2
    if args.sweep:
        name = session.target.name or session.target.username or ""
        variants = gen_usernames(name)
        if session.target.username and session.target.username not in variants:
            variants.insert(0, session.target.username)
        session.usernames_checked = variants
        session.username_hits = checkers.sweep(
            variants, threads=args.threads, timeout=args.timeout)
        for hit in session.username_hits:
            print(f"[hit] {hit['username']} @ {hit['site']}: {hit['url']}")
    if args.dorks:
        config = dorks.DorkConfig(
            filetypes=["pdf", "csv", "txt", "env", "log"],
            sites=[label for label, _ in dorks.SITE_TABLE[:6]],
            modifiers=["exact phrase"], include_leaks=True)
        session.dorks = dorks.build(session.target, config)
        for dork in session.dorks:
            print(f"[dork] {dork}")
    if args.save:
        md_path, json_path = report.save(session, args.save)
        print(f"saved: {md_path}  {json_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.no_color:
        ui.COLOR = False
    # Non-interactive paths never prompt.
    if args.help_backends or args.status:
        return _noninteractive(args)
    if any((args.sweep, args.dorks, args.save)):
        return _noninteractive(args)
    try:
        return _interactive(args)
    except KeyboardInterrupt:
        print()
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
