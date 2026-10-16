#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dc2_pcmes.py — D.C.II P.C. (Da Capo II Plus Communication, PC 18+) MES Tool.

Reverse-engineered from DC2PC.EXE (loader at 0x0041E440, tokenizer at 0x0041AF30,
encstr decipher at 0x004241F0 / 0x00424AF4) and verified against all 1,558 PC scripts
in DC2PC/AdvData/MES/*.mes.

File Format (PC MES version 0x9969):
------------------------------------
  int32   label_count
  int32   labels[label_count]     # raw label values == (bytecode token offset + 2)
  uint16  version                 # 0x9969 (little endian: low byte 0x69, high byte 0x99)
  bytecode...

Token Opcode Classes (0x9969):
------------------------------
  0x00 - 0x28 : uint8x2   [op:1B][arg1:1B][arg2:1B]                     (3 bytes)
  0x29 - 0x2E : uint8str  [op:1B][arg1:1B][str:NUL-terminated]
  0x2F - 0x49 : string    [op:1B][str:NUL-terminated]
  0x4A - 0x4D : encstr    [op:1B][cipher_str:NUL-terminated]
                          plain byte = (cipher byte + 0x20) & 0xFF
                          cipher byte = (plain byte - 0x20) & 0xFF
  0x4E - 0xFF : uint16x4  [op:1B][4 x uint16 LE]                        (9 bytes)

Dialogue Opcodes:
-----------------
  0x4B : encstr -> speaker name (e.g. "さくら", "義之")
  0x4C : encstr -> dialogue message text (newline = 0x0A)
  0x4D : encstr -> choice option text
  0x45 : string -> extra scene / title strings

Subcommands:
------------
  dump    MES_DIR_OR_FILE OUT.json     Dump dialogue & choices to JSON.
  import  IN.json MES_DIR OUT_DIR      Rebuild .mes files from edited JSON.
  verify  MES_DIR                      Parse and test round-trip on all .mes files.
"""

import sys
import os
import struct
import json
import argparse

MES_VERSION = 0x9969
SJIS = "cp932"

# Token opcode ranges
U8X2_LO, U8X2_HI = 0x00, 0x28
U8STR_LO, U8STR_HI = 0x29, 0x2E
STR_LO, STR_HI = 0x2F, 0x49
ENCSTR_LO, ENCSTR_HI = 0x4A, 0x4D
U16X4_LO, U16X4_HI = 0x4E, 0xFF

# Dialogue opcodes
NAME_OP = 0x4B
MSG_OP = 0x4C
CHOICE_OP = 0x4D
EXTRA_STR_OP = 0x45


def decrypt(b: bytes) -> bytes:
    """Decrypt encstr: plain = cipher + 0x20."""
    return bytes((x + 0x20) & 0xFF for x in b)


def encrypt(b: bytes) -> bytes:
    """Encrypt encstr: cipher = plain - 0x20."""
    return bytes((x - 0x20) & 0xFF for x in b)


def parse_mes(blob: bytes):
    """
    Parse a PC .mes script (version 0x9969).
    Returns:
      header : bytes (everything before bytecode, incl. label table & version)
      labels : list[int] (raw label target offsets)
      tokens : list of (offset:int, op:int, length:int, s:bytes|None, raw:bytes)
    """
    if len(blob) < 8:
        raise ValueError(".mes file too small (< 8 bytes)")

    (label_count,) = struct.unpack_from("<i", blob, 0)
    if label_count < 0 or label_count > 1_000_000:
        raise ValueError(f"Invalid label_count {label_count}")

    voff = 4 + label_count * 4
    if len(blob) < voff + 2:
        raise ValueError(".mes truncated header")

    version = struct.unpack_from("<H", blob, voff)[0]
    if version != MES_VERSION:
        raise ValueError(f"Unsupported MES version 0x{version:04X} (expected 0x{MES_VERSION:04X})")

    labels = [struct.unpack_from("<i", blob, 4 + i * 4)[0] for i in range(label_count)]
    bc_start = voff + 2
    bc = blob[bc_start:]

    tokens = []
    i = 0
    n = len(bc)
    while i < n:
        op = bc[i]
        if U8X2_LO <= op <= U8X2_HI:
            ln = 3
            s = None
        elif U8STR_LO <= op <= U8STR_HI:
            null_pos = bc.find(b"\x00", i + 2)
            if null_pos == -1:
                raise ValueError(f"Unterminated uint8str token at 0x{i:X}")
            ln = null_pos - i + 1
            s = bc[i + 2:null_pos]
        elif STR_LO <= op <= STR_HI:
            null_pos = bc.find(b"\x00", i + 1)
            if null_pos == -1:
                raise ValueError(f"Unterminated string token at 0x{i:X}")
            ln = null_pos - i + 1
            s = bc[i + 1:null_pos]
        elif ENCSTR_LO <= op <= ENCSTR_HI:
            null_pos = bc.find(b"\x00", i + 1)
            if null_pos == -1:
                raise ValueError(f"Unterminated encstr token at 0x{i:X}")
            ln = null_pos - i + 1
            s = bc[i + 1:null_pos]
        elif U16X4_LO <= op <= U16X4_HI:
            ln = 9
            s = None
        else:
            raise ValueError(f"Unknown opcode 0x{op:02X} at offset 0x{i:X}")

        if i + ln > n:
            raise ValueError(f"Truncated token 0x{op:02X} at offset 0x{i:X}")

        tokens.append((i, op, ln, s, bc[i:i + ln]))
        i += ln

    return blob[:bc_start], labels, tokens


def rebuild_mes(header: bytes, labels: list[int], tokens: list, replacements: dict) -> bytes:
    """
    Rebuild .mes script.
    `replacements`: token_offset -> new_raw_bytes (without opcode or null terminator).
    Labels are recalculated based on new token lengths.
    """
    bc = bytearray()
    new_labels = list(labels)
    label_index = 0

    for (off, op, _ln, _s, raw) in tokens:
        # Check label target match (label points to token offset + 2)
        while label_index < len(new_labels) and off + 2 == new_labels[label_index]:
            new_labels[label_index] = len(bc) + 2
            label_index += 1

        if off in replacements:
            bc.append(op)
            bc += replacements[off]
            bc.append(0)
        else:
            bc += raw

    # Check remaining labels if any
    while label_index < len(new_labels):
        new_labels[label_index] = len(bc) + 2
        label_index += 1

    out = bytearray(header)
    for i, lbl in enumerate(new_labels):
        struct.pack_into("<i", out, 4 + i * 4, lbl)
    out += bc
    return bytes(out)


def extract_dialogue(blob: bytes) -> list[dict]:
    """Extract dialogue lines, speaker names, choices, and text entries."""
    _header, _labels, tokens = parse_mes(blob)
    lines = []
    cur_name = ""
    cur_name_offset = None

    for (off, op, _ln, s, _raw) in tokens:
        if op == NAME_OP:
            cur_name = decrypt(s).decode(SJIS, errors="replace")
            cur_name_offset = off
        elif op == MSG_OP:
            lines.append({
                "type": "dialogue",
                "name": cur_name,
                "message": decrypt(s).decode(SJIS, errors="replace"),
                "name_offset": cur_name_offset,
                "message_offset": off,
            })
        elif op == CHOICE_OP:
            lines.append({
                "type": "choice",
                "name": "",
                "message": decrypt(s).decode(SJIS, errors="replace"),
                "name_offset": None,
                "message_offset": off,
            })
        elif op == EXTRA_STR_OP:
            text = s.decode(SJIS, errors="replace")
            if any(ord(c) > 0x7F for c in text):
                lines.append({
                    "type": "text",
                    "name": "",
                    "message": text,
                    "name_offset": None,
                    "message_offset": off,
                })

    return lines


def cmd_dump(input_path: str, out_json: str):
    """Dump scripts to JSON."""
    scripts = []
    if os.path.isfile(input_path):
        files = [input_path]
        base_dir = os.path.dirname(input_path)
    else:
        files = [os.path.join(input_path, f) for f in os.listdir(input_path) if f.lower().endswith(".mes")]
        base_dir = input_path

    total_lines = 0
    for f in sorted(files):
        fname = os.path.basename(f)
        try:
            blob = open(f, "rb").read()
            lines = extract_dialogue(blob)
        except Exception as e:
            print(f"Error reading {fname}: {e}", file=sys.stderr)
            continue

        if lines:
            scripts.append({"file": fname, "lines": lines})
            total_lines += len(lines)

    data = {
        "game": "D.C.II P.C. (Da Capo II Plus Communication)",
        "version": f"0x{MES_VERSION:04X}",
        "total_scripts": len(scripts),
        "total_lines": total_lines,
        "scripts": scripts,
    }

    with open(out_json, "w", encoding="utf-8") as out:
        json.dump(data, out, ensure_ascii=False, indent=2)

    print(f"Dumped {total_lines} lines across {len(scripts)} scripts -> {out_json}")


def cmd_import(in_json: str, mes_dir: str, out_dir: str):
    """Rebuild .mes files from JSON into out_dir."""
    with open(in_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    os.makedirs(out_dir, exist_ok=True)
    by_file = {}
    for item in data.get("scripts", []):
        name = item["file"]
        reps = {}
        for entry in item.get("lines", []):
            etype = entry.get("type", "dialogue")
            name_text = entry.get("name")
            msg_text = entry.get("message")
            name_off = entry.get("name_offset")
            msg_off = entry.get("message_offset")

            if name_off is not None and name_text:
                raw_name = name_text.encode(SJIS, errors="replace")
                reps[name_off] = encrypt(raw_name)

            if msg_off is not None and msg_text is not None:
                raw_msg = msg_text.encode(SJIS, errors="replace")
                if etype in ("dialogue", "choice"):
                    reps[msg_off] = encrypt(raw_msg)
                else:
                    reps[msg_off] = raw_msg

        by_file[name.lower()] = reps

    files = [f for f in os.listdir(mes_dir) if f.lower().endswith(".mes")]
    written = 0
    modified = 0

    for fname in files:
        in_path = os.path.join(mes_dir, fname)
        out_path = os.path.join(out_dir, fname)
        blob = open(in_path, "rb").read()

        reps = by_file.get(fname.lower())
        if reps:
            header, labels, tokens = parse_mes(blob)
            rebuilt = rebuild_mes(header, labels, tokens, reps)
            with open(out_path, "wb") as out:
                out.write(rebuilt)
            modified += 1
        else:
            with open(out_path, "wb") as out:
                out.write(blob)
        written += 1

    print(f"Done: {written} scripts written to {out_dir} ({modified} modified).")


def cmd_verify(mes_dir: str):
    """Verify bit-perfect parsing and reconstruction on all .mes files in mes_dir."""
    files = [f for f in os.listdir(mes_dir) if f.lower().endswith(".mes")]
    print(f"Verifying {len(files)} scripts in {mes_dir}...")
    errors = 0
    mismatches = 0
    total_tokens = 0
    total_labels = 0

    for idx, fname in enumerate(files):
        p = os.path.join(mes_dir, fname)
        blob = open(p, "rb").read()
        try:
            hdr, labels, tokens = parse_mes(blob)
            total_tokens += len(tokens)
            total_labels += len(labels)
            rebuilt = rebuild_mes(hdr, labels, tokens, {})
            if rebuilt != blob:
                print(f"Mismatch on {fname}!")
                mismatches += 1
        except Exception as e:
            print(f"Error on {fname}: {e}")
            errors += 1

    print(f"Verification complete: {len(files)} scripts, {total_tokens} tokens, {total_labels} labels.")
    print(f"Errors: {errors}, Mismatches: {mismatches}")
    if errors == 0 and mismatches == 0:
        print("ALL SCRIPTS PASSED BIT-PERFECT ROUND-TRIP!")


def main():
    parser = argparse.ArgumentParser(description="D.C.II P.C. MES script tool")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_dump = sub.add_parser("dump", help="Dump text to JSON")
    p_dump.add_argument("input", help="MES directory or single file")
    p_dump.add_argument("output", help="Output JSON path")

    p_import = sub.add_parser("import", help="Import text from JSON into .mes files")
    p_import.add_argument("json", help="Input JSON path")
    p_import.add_argument("mesdir", help="Directory containing original .mes files")
    p_import.add_argument("outdir", help="Directory to save rebuilt .mes files")

    p_verify = sub.add_parser("verify", help="Verify round-trip of MES directory")
    p_verify.add_argument("mesdir", help="Directory containing .mes files")

    args = parser.parse_args()
    if args.cmd == "dump":
        cmd_dump(args.input, args.output)
    elif args.cmd == "import":
        cmd_import(args.json, args.mesdir, args.outdir)
    elif args.cmd == "verify":
        cmd_verify(args.mesdir)


if __name__ == "__main__":
    main()
