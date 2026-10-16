#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dc2_mes.py — D.C.II P.S. (Da Capo II Plus Situation, SLPM-669.22) MES.DAT tool.

Reverse-engineered from the game binary (interpreter sub_10DB48) and cross-checked
against MesTextTool (Circus Engine). Targets the *PS2* script format version 0x6E7D.

Subcommands
-----------
  extract  MES.DAT OUTDIR          Extract every *.MES script from MES.DAT.
  dump     MES.DAT OUT.json        Dump all dialogue to JSON {name, message} (plus
                                   choices / system text).
  import   IN.json MES.DAT OUT.DAT Rebuild MES.DAT from translated JSON + original DAT.
  pack     MESDIR OUT.DAT          Repack a directory of *.MES files into MES.DAT.

Formats (documentation)
-----------------------
MES.DAT (archive):
    uint32 count
    count x { uint32 offset, uint32 size }   (front table; redundant, unused for lookup)
    count x { char name[56]; uint32 offset; uint32 size; }   (64-byte entries)
    pad to 0x800
    file data (each entry: `size` bytes of data + 4-byte checksum, then 0x800-padded)

The game (sub_103CB0) binary-searches the 64-byte name entries and reads
`offset` at +56 / `size` at +60 *from the name entry itself*; the front
table is never consulted for lookups. Entries are sorted in memory at load
(sub_140B38), so on-disk order does not matter.

Every entry carries a 4-byte checksum immediately after its `size` bytes of
data (verified by sub_1041B0). If the checksum does not match the game
prints "readed data error" and refuses the file. Layout per entry:
    [ data : size bytes ][ checksum : 4 bytes ][ pad to 0x800 ]
Checksum (16-bit each, little-endian hi/lo byte order):
    sum  = sum(data bytes)
    acc  = sum((byte ^ 0xE5) << (index % 4))
    bytes = [sum>>8, sum&0xFF, acc>>8, acc&0xFF]

.MES (script):
    int32  label_count
    int32  labels[label_count]               (label values == bytecode offset + 2)
    uint16 version                            (== 0x6E7D for this game)
    bytecode...

Bytecode opcodes:
    0x00-0x2E  uint8x2   1 byte op + 2 byte args                     (3 bytes)
    0x2F-0x35  uint8str  1 byte op + 1 byte arg + NUL-terminated str
    0x36-0x58  string    1 byte op + NUL-terminated string
    0x59-0x5C  encstr    like `string`, but every byte is stored -0x20
                          (i.e. plain = cipher + 0x20)
    0x5D-0xFF  uint16x4  1 byte op + 4 x uint16                      (9 bytes)

Dialogue opcodes (this game):
    0x5A  encstr -> speaker name
    0x5B  encstr -> message text (newline = 0x0A byte)
    0x5C  encstr -> choice text
    0x4F  string -> system menu text
    0x51  string -> mixed (script ids + some scene text)
    0x57  string -> system text

Strings are Shift-JIS. On import, the label table is rewritten to account for
changed text lengths (jump opcodes reference labels by *index*, so only the
label array needs fixing).

IMPORTANT — encryption constraints on 0x59-0x5C (name/message/choice) strings:
  cipher = plain - 0x20 (mod 256), and strings are NUL-terminated. Therefore
  * a plain 0x20 (ASCII space) would encrypt to 0x00 (the terminator) — NOT
    representable. The game uses fullwidth space 0x8140 (U+3000) instead.
  * a plain 0x24 ("$") would decrypt back to "$", which the game's string
    reader (sub_10DAF8) treats as a 2-byte inline escape.
On import we therefore convert ASCII space -> fullwidth space and "$" ->
fullwidth "＄" automatically, and print a warning when this happens.
"""

import argparse
import json
import os
import struct
import sys

# ---------------------------------------------------------------------------
# Format constants
# ---------------------------------------------------------------------------
MES_VERSION = 0x6E7D
ENC_KEY = 0x20                 # plain = cipher + 0x20 (mod 256)
SJIS = "shift_jis"

# opcode ranges
U8X2_LO, U8X2_HI = 0x00, 0x2E   # op + 2 bytes
U8STR_LO, U8STR_HI = 0x2F, 0x35  # op + 1 byte + string
STR_LO, STR_HI = 0x36, 0x58     # op + string
ENCSTR_LO, ENCSTR_HI = 0x59, 0x5C  # op + encrypted string
U16X4_LO = 0x5D                 # op + 4 x uint16

NAME_OP = 0x5A
MSG_OP = 0x5B
CHOICE_OP = 0x5C

# string opcodes whose Japanese payload we also export as translatable text
EXTRA_TEXT_OPS = {0x4F, 0x51, 0x57}

ALIGN = 0x800
NAME_FIELD = 56   # name bytes inside a name entry (NUL-terminated)
ENTRY_LEN = 64    # name[56] + uint32 offset + uint32 size


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------
def decrypt(b):
    """plain = cipher + key (mod 256)"""
    return bytes((c + ENC_KEY) & 0xFF for c in b)


def encrypt(b):
    """cipher = plain - key (mod 256)"""
    return bytes((c - ENC_KEY) & 0xFF for c in b)


def align_up(n, a=ALIGN):
    return (n + a - 1) // a * a


def checksum(blob):
    """4-byte Circus archive entry checksum (verified by sub_1041B0)."""
    s = 0
    i = 0
    for idx, b in enumerate(blob):
        s = (s + b) & 0xFFFF
        i = (i + ((b ^ 0xE5) << (idx % 4))) & 0xFFFF
    return bytes([(s >> 8) & 0xFF, s & 0xFF, (i >> 8) & 0xFF, i & 0xFF])


def sanitize(text_bytes):
    """Make SJIS text safe for the +0x20 cipher (see module docstring).
    Returns (bytes, warning_message_or_None)."""
    n_space = text_bytes.count(0x20)
    n_dollar = text_bytes.count(0x24)
    out = text_bytes.replace(b"\x20", "\u3000".encode(SJIS)) \
                    .replace(b"\x24", "＄".encode(SJIS))
    if n_space or n_dollar:
        return out, (f"converted {n_space} ASCII space(s) -> fullwidth space, "
                     f"{n_dollar} '$' -> fullwidth ＄")
    return out, None


# ---------------------------------------------------------------------------
# MES.DAT archive
# ---------------------------------------------------------------------------
def parse_mes_dat(data):
    """Return list of (name:str, offset:int, size:int, blob:bytes)."""
    if len(data) < 4:
        raise ValueError("MES.DAT too small")
    (count,) = struct.unpack_from("<I", data, 0)
    entries = []
    name_base = 4 + count * 8
    for i in range(count):
        off, size = struct.unpack_from("<II", data, 4 + i * 8)
        raw_name = data[name_base + i * ENTRY_LEN:name_base + i * ENTRY_LEN + NAME_FIELD]
        name = raw_name.split(b"\x00", 1)[0].decode(SJIS, "replace")
        entries.append((name, off, size, data[off:off + size]))
    return entries


def build_mes_dat(entries):
    """entries: list of (name:str, blob:bytes). Returns MES.DAT bytes."""
    count = len(entries)
    header = bytearray(struct.pack("<I", count))
    table_pos = 4
    header += b"\x00" * (count * 8)                 # front offset/size table (later)
    embedded_pos = []                               # offset of each entry's +56 field
    for name, _blob in entries:
        name_b = name.encode(SJIS, "replace")
        if len(name_b) > NAME_FIELD - 1:
            name_b = name_b[:NAME_FIELD - 1]
        embedded_pos.append(len(header) + NAME_FIELD)
        header += name_b + b"\x00" * (NAME_FIELD - len(name_b))
        header += b"\x00" * 8                       # offset+size, filled later
    data_start = align_up(len(header))
    header += b"\x00" * (data_start - len(header))  # pad to ALIGN

    out = bytearray(header)
    table = []
    for _name, blob in entries:
        off = len(out)
        out += blob
        out += checksum(blob)                      # 4-byte per-entry checksum
        out += b"\x00" * (align_up(len(out)) - len(out))
        table.append((off, len(blob)))
    for i, (off, size) in enumerate(table):
        struct.pack_into("<II", out, table_pos + i * 8, off, size)  # front table
        struct.pack_into("<II", out, embedded_pos[i], off, size)    # embedded copy
    return bytes(out)


# ---------------------------------------------------------------------------
# .MES script
# ---------------------------------------------------------------------------
def parse_mes(blob):
    """
    Parse a .mes script. Returns:
      header : bytes (everything before the bytecode, incl. label table)
      labels : list[int] (raw label values)
      tokens : list of (offset:int, op:int, length:int, string:bytes|None, raw:bytes)
               offset is relative to the start of the bytecode.
               raw is the complete token bytes (op + payload) for verbatim copy.
    """
    if len(blob) < 8:
        raise ValueError(".mes too small")
    (label_count,) = struct.unpack_from("<i", blob, 0)
    if label_count < 0 or label_count > 1_000_000:
        raise ValueError("bad label_count %r" % label_count)
    voff = label_count * 4 + 4
    if len(blob) < voff + 2:
        raise ValueError(".mes truncated header")
    version = struct.unpack_from("<H", blob, voff)[0]
    # version high byte varies by script subsystem (0x6E scenario, 0x6A CG/DB,
    # 0x2B menu, 0x30 ...); the low byte 0x7D is the engine format and is
    # constant. The opcode layout is identical across all of them.
    labels = [struct.unpack_from("<i", blob, 4 + i * 4)[0] for i in range(label_count)]
    bc_start = voff + 2
    bc = blob[bc_start:]

    tokens = []
    i = 0
    n = len(bc)
    while i < n:
        op = bc[i]
        if U8X2_LO <= op <= U8X2_HI:
            ln, s = 3, None
        elif U8STR_LO <= op <= U8STR_HI:
            s = bc[i + 2:].split(b"\x00", 1)[0]
            ln = 3 + len(s)
        elif STR_LO <= op <= STR_HI:
            s = bc[i + 1:].split(b"\x00", 1)[0]
            ln = 2 + len(s)
        elif ENCSTR_LO <= op <= ENCSTR_HI:
            s = bc[i + 1:].split(b"\x00", 1)[0]
            ln = 2 + len(s)
        elif op >= U16X4_LO:
            ln, s = 9, None
        else:
            raise ValueError(f"unhandled opcode 0x{op:02X} at bytecode offset {i}")
        if i + ln > n:
            raise ValueError(f"truncated token 0x{op:02X} at bytecode offset {i}")
        tokens.append((i, op, ln, s, bc[i:i + ln]))
        i += ln
    return blob[:bc_start], labels, tokens


def rebuild_mes(header, labels, tokens, replacements):
    """
    Rebuild a .mes script. `replacements` maps bytecode token offset -> new raw
    string bytes (already encrypted where required). Tokens are copied verbatim
    except replaced ones. The label table is rewritten for the new lengths.
    """
    bc = bytearray()
    new_labels = list(labels)
    label_index = 0
    for (off, op, _ln, _s, raw) in tokens:
        # labels are stored as (bytecode offset + 2 == version token length)
        if label_index < len(new_labels) and off + 2 == new_labels[label_index]:
            new_labels[label_index] = len(bc) + 2
            label_index += 1

        if off in replacements:
            bc.append(op)
            bc += replacements[off]
            bc.append(0)
        else:
            bc += raw

    out = bytearray(header)
    for i, lbl in enumerate(new_labels):
        struct.pack_into("<i", out, 4 + i * 4, lbl)
    out += bc
    return bytes(out)


# ---------------------------------------------------------------------------
# Dialogue extraction (the important part)
# ---------------------------------------------------------------------------
def extract_dialogue(blob):
    """Walk a .mes script, returning a list of line dicts."""
    _header, _labels, tokens = parse_mes(blob)
    lines = []
    cur_name = ""
    cur_name_offset = None
    for (off, op, _ln, s, _raw) in tokens:
        if op == NAME_OP:
            cur_name = decrypt(s).decode(SJIS, "replace")
            cur_name_offset = off
        elif op == MSG_OP:
            lines.append({
                "type": "dialogue",
                "name": cur_name,
                "message": decrypt(s).decode(SJIS, "replace"),
                "name_offset": cur_name_offset,
                "message_offset": off,
            })
        elif op == CHOICE_OP:
            lines.append({
                "type": "choice",
                "name": "",
                "message": decrypt(s).decode(SJIS, "replace"),
                "name_offset": None,
                "message_offset": off,
            })
        elif op in EXTRA_TEXT_OPS:
            text = s.decode(SJIS, "replace")
            if any(ord(c) > 0x7F for c in text):
                lines.append({
                    "type": "system" if op in (0x4F, 0x57) else "text",
                    "name": "",
                    "message": text,
                    "name_offset": None,
                    "message_offset": off,
                })
    return lines


def dump_json(mes_dat_path, out_json):
    with open(mes_dat_path, "rb") as f:
        data = f.read()
    entries = parse_mes_dat(data)
    files = []
    total = 0
    for name, _off, _size, blob in entries:
        try:
            lines = extract_dialogue(blob)
        except Exception as e:
            print(f"  skip {name}: {e}", file=sys.stderr)
            continue
        if lines:
            files.append({"file": name, "lines": lines})
            total += len(lines)
    out = {
        "game": "D.C.II P.S. - Da Capo II - Plus Situation (Disc 1)",
        "version": "0x%04X" % MES_VERSION,
        "encoding": SJIS,
        "encryption": {"mode": "add", "key": ENC_KEY},
        "files": files,
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"wrote {out_json}: {len(files)} files, {total} lines")


# ---------------------------------------------------------------------------
# Import (JSON -> new MES.DAT)
# ---------------------------------------------------------------------------
def import_json(in_json, mes_dat_path, out_dat):
    with open(in_json, "r", encoding="utf-8") as f:
        doc = json.load(f)
    with open(mes_dat_path, "rb") as f:
        data = f.read()
    entries = parse_mes_dat(data)

    by_file = {}
    for fd in doc.get("files", []):
        fn = fd["file"]
        repl = {}
        for line in fd.get("lines", []):
            text = line.get("message")
            if text is None:
                continue
            moff = line.get("message_offset")
            noff = line.get("name_offset")
            if moff is not None:
                repl[moff] = ("msg", text)
            if noff is not None:
                repl[noff] = ("name", line.get("name") or "")
        by_file[fn] = repl

    new_entries = []
    changed = 0
    sanitized = 0
    for name, _off, _size, blob in entries:
        if name not in by_file:
            new_entries.append((name, blob))
            continue
        header, labels, tokens = parse_mes(blob)
        replacements = {}
        for (off, op, _ln, _s, _raw) in tokens:
            r = by_file[name].get(off)
            if r is None:
                continue
            _kind, text = r
            # names/messages/choices are stored encrypted; plain opcodes aren't
            if op in (NAME_OP, MSG_OP, CHOICE_OP):
                sjis = text.encode(SJIS, "replace")
                sjis, warn = sanitize(sjis)
                if warn:
                    sanitized += 1
                    print(f"  {name} @0x{off:X}: {warn}", file=sys.stderr)
                raw = encrypt(sjis)
            else:
                raw = text.encode(SJIS, "replace")
            replacements[off] = raw
        if replacements:
            new_entries.append((name, rebuild_mes(header, labels, tokens, replacements)))
            changed += 1
        else:
            new_entries.append((name, blob))

    with open(out_dat, "wb") as f:
        f.write(build_mes_dat(new_entries))
    print(f"wrote {out_dat}: {changed} files modified, {len(new_entries)} total")
    if sanitized:
        print(f"  note: {sanitized} strings had ASCII spaces / '$' converted "
              f"(spaces cannot be stored in encrypted text)",
              file=sys.stderr)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(description="D.C.II P.S. MES.DAT tool")
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("extract", help="extract .mes files from MES.DAT")
    e.add_argument("mes_dat")
    e.add_argument("outdir")

    d = sub.add_parser("dump", help="dump dialogue to JSON {name,message}")
    d.add_argument("mes_dat")
    d.add_argument("out_json")

    i = sub.add_parser("import", help="rebuild MES.DAT from translated JSON")
    i.add_argument("in_json")
    i.add_argument("mes_dat")
    i.add_argument("out_dat")

    k = sub.add_parser("pack", help="repack a directory of .mes files")
    k.add_argument("mesdir")
    k.add_argument("out_dat")

    a = p.parse_args()
    if a.cmd == "extract":
        with open(a.mes_dat, "rb") as f:
            data = f.read()
        os.makedirs(a.outdir, exist_ok=True)
        n = 0
        for name, _off, _size, blob in parse_mes_dat(data):
            with open(os.path.join(a.outdir, name), "wb") as f:
                f.write(blob)
            n += 1
        print(f"extracted {n} files -> {a.outdir}")
    elif a.cmd == "dump":
        dump_json(a.mes_dat, a.out_json)
    elif a.cmd == "import":
        import_json(a.in_json, a.mes_dat, a.out_dat)
    elif a.cmd == "pack":
        names = sorted(fn for fn in os.listdir(a.mesdir) if fn.lower().endswith(".mes"))
        entries = []
        for fn in names:
            with open(os.path.join(a.mesdir, fn), "rb") as f:
                entries.append((fn, f.read()))
        with open(a.out_dat, "wb") as f:
            f.write(build_mes_dat(entries))
        print(f"packed {len(entries)} files -> {a.out_dat}")


if __name__ == "__main__":
    main()
