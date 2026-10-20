# assets

Branding for magnify.

## Files

| File | Purpose |
|---|---|
| `logo.png` (or `logo.svg`) | Main logo, shown at the top of the project README |

## Adding your logo

1. Drop the file in this directory.
2. If you name it anything other than `logo.png`, update the `<img src=...>`
   path in the top of the project `README.md`.

Prefer SVG when you have one — it stays sharp at any size and is usually
a fraction of the file size of a PNG.

## Terminal banner

The ASCII art shown when you *run* the tool lives in
`magnify/ui.py` in the `banner()` function — it is separate from this
logo. Replace the `art = r""" ... """` block there if you want the
startup banner to match.
