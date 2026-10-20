"""Minimal DNS client over UDP using only the standard library.

Used for MX/TXT lookups (SPF, DMARC) so magnify has zero external
dependencies. Supports compression-pointer name decoding; falls back
to the system resolver via /etc/resolv.conf.
"""

from __future__ import annotations

import random
import socket
import struct

TYPE_A = 1
TYPE_NS = 2
TYPE_CNAME = 5
TYPE_MX = 15
TYPE_TXT = 16
TYPE_AAAA = 28

_QTYPE_NAMES = {TYPE_A: "A", TYPE_MX: "MX", TYPE_TXT: "TXT", TYPE_AAAA: "AAAA"}


def _resolv_nameservers() -> list[str]:
    servers = ["1.1.1.1", "8.8.8.8"]
    try:
        with open("/etc/resolv.conf", encoding="utf-8") as fh:
            for line in fh:
                parts = line.split()
                if len(parts) >= 2 and parts[0] == "nameserver":
                    servers.insert(0, parts[1])
    except OSError:
        pass
    # de-dup, keep order
    seen: set[str] = set()
    out = []
    for s in servers:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def _encode_name(name: str) -> bytes:
    out = b""
    for label in name.rstrip(".").split("."):
        raw = label.encode("idna") if label else b""
        out += bytes([len(raw)]) + raw
    return out + b"\x00"


def _decode_name(buf: bytes, offset: int) -> tuple[str, int]:
    """Decode a possibly-compressed name; returns (name, next_offset)."""
    labels: list[str] = []
    jumped = False
    start = offset
    hops = 0
    while True:
        if offset >= len(buf):
            raise ValueError("truncated DNS name")
        length = buf[offset]
        if length == 0:
            offset += 1
            break
        if length & 0xC0 == 0xC0:  # compression pointer
            if offset + 1 >= len(buf):
                raise ValueError("truncated DNS pointer")
            ptr = ((length & 0x3F) << 8) | buf[offset + 1]
            if not jumped:
                start = offset + 2
            jumped = True
            offset = ptr
            hops += 1
            if hops > 32:
                raise ValueError("DNS pointer loop")
            continue
        offset += 1
        labels.append(buf[offset:offset + length].decode("utf-8", "replace"))
        offset += length
    return ".".join(labels), (start if jumped else offset)


def query(name: str, qtype: int = TYPE_MX, timeout: float = 4.0,
          server: str | None = None) -> list[tuple[int, object]]:
    """Send a DNS query, return list of (type, value) answers.

    MX  -> (TYPE_MX, (priority, exchange))
    TXT -> (TYPE_TXT, str)
    A   -> (TYPE_A, str ip)
    """
    txid = random.randint(0, 0xFFFF)
    header = struct.pack(">HHHHHH", txid, 0x0100, 1, 0, 0, 0)
    question = _encode_name(name) + struct.pack(">HH", qtype, 1)
    packet = header + question

    servers = [server] if server else _resolv_nameservers()
    last_exc: Exception | None = None
    for srv in servers:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            sock.sendto(packet, (srv, 53))
            buf, _ = sock.recvfrom(4096)
            sock.close()
            return _parse_response(buf, txid)
        except (OSError, ValueError) as exc:
            last_exc = exc
            continue
    if last_exc:
        raise OSError(f"DNS query for {name!r} failed: {last_exc}")
    return []


def _parse_response(buf: bytes, txid: int) -> list[tuple[int, object]]:
    if len(buf) < 12:
        raise ValueError("short DNS response")
    rxid, flags, qdcount, ancount, _ns, _ar = struct.unpack(">HHHHHH", buf[:12])
    if rxid != txid:
        raise ValueError("DNS txid mismatch")
    rcode = flags & 0x000F
    if rcode == 3:  # NXDOMAIN
        return []
    if rcode != 0:
        raise ValueError(f"DNS rcode {rcode}")

    offset = 12
    for _ in range(qdcount):
        _, offset = _decode_name(buf, offset)
        offset += 4

    answers: list[tuple[int, object]] = []
    for _ in range(ancount):
        _, offset = _decode_name(buf, offset)
        if offset + 10 > len(buf):
            break
        rtype, _rclass, _ttl, rdlength = struct.unpack(
            ">HHIH", buf[offset:offset + 10])
        offset += 10
        rdata_start = offset
        rdata = buf[offset:offset + rdlength]
        offset += rdlength
        if rtype == TYPE_MX and len(rdata) >= 3:
            priority = struct.unpack(">H", rdata[:2])[0]
            exchange, _ = _decode_name(buf, rdata_start + 2)
            answers.append((TYPE_MX, (priority, exchange)))
        elif rtype == TYPE_TXT:
            texts = []
            i = 0
            while i < len(rdata):
                ln = rdata[i]
                texts.append(rdata[i + 1:i + 1 + ln].decode("utf-8", "replace"))
                i += 1 + ln
            answers.append((TYPE_TXT, "".join(texts)))
        elif rtype == TYPE_A and len(rdata) == 4:
            answers.append((TYPE_A, socket.inet_ntoa(rdata)))
        elif rtype == TYPE_CNAME:
            cname, _ = _decode_name(buf, offset - rdlength)
            answers.append((TYPE_CNAME, cname))
    return answers


def mx_records(domain: str) -> list[tuple[int, str]]:
    answers = query(domain, TYPE_MX)
    records = [v for t, v in answers if t == TYPE_MX]
    records.sort(key=lambda item: item[0])
    return records


def txt_records(domain: str) -> list[str]:
    answers = query(domain, TYPE_TXT)
    return [v for t, v in answers if t == TYPE_TXT]


def qtype_name(qtype: int) -> str:
    return _QTYPE_NAMES.get(qtype, str(qtype))
