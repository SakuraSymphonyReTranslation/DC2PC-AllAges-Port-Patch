#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dc2_transcode.py — transcode a PS2 MES script (0x6E7D) into PC MES (0x9969).

Uses the learned opcode map (opcode_map2.json) produced by dc2_learnmap2.py.

Token shapes are identical between versions:
  u8x2   op+2B   (PS2 0x00-0x2E | PC 0x00-0x28)
  u8str  op+arg+str          (PS2 0x2F-0x35 | PC 0x29-0x2E)
  str    op+str              (PS2 0x36-0x58 | PC 0x2F-0x49)
  encstr op+str  (+0x20)     (PS2 0x59-0x5C | PC 0x4A-0x4D)
  u16x4  op+4xu16 (PS2 0x5D+ | PC 0x4E+)

Transcode rules:
  - map opcode via table (unmapped ops -> error or keep, --strict)
  - remap payload ops: string stays string, encstr stays encstr, u16x4 stays
  - recompute label table: labels reference token offsets (+2); since the
    label array is *parallel* (referenced by index from jump ops), we
    recompute label values to point at the same *token index* in the new
    stream, preserving control flow 1:1.

NOTE: PC token classes have different opcode ranges.  When a PS2 op maps to a
PC op of a DIFFERENT class (e.g. PS2 str -> PC u8str), the payload layout
changes (str: op+str, u8str: op+arg+str).  The learned map handles the ops we
observed; new combos must be added to the map or the script will fail --strict.

Usage:
  python tools/dc2_transcode.py IN.mes OUT.mes [--map opcode_map2.json] [--strict]
"""

import argparse
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dc2_mes      # noqa: E402
import dc2_pcmes    # noqa: E402


def load_map(path):
    m = json.load(open(path))
    out = {}
    for k, v in m.items():
        out[int(k, 16)] = int(v["best"], 16)
    return out


def classify(op, vers="ps2"):
    if vers == "ps2":
        if op <= 0x2E: return "u8x2"
        if op <= 0x35: return "u8str"
        if op <= 0x58: return "str"
        if op <= 0x5C: return "encstr"
        return "u16x4"
    else:
        if op <= 0x28: return "u8x2"
        if op <= 0x2E: return "u8str"
        if op <= 0x49: return "str"
        if op <= 0x4D: return "encstr"
        return "u16x4"


def transcode(blob: bytes, opmap: dict, strict: bool = True):
    header, labels, tokens = dc2_mes.parse_mes(blob)
    label_count = struct.unpack_from("<i", header, 0)[0]

    # map: original bytecode offset -> token index (for label retargeting)
    off_to_idx = {off: i for i, (off, op, ln, s, raw) in enumerate(tokens)}
    # label raw values = bytecode offset + 2 (PS2) -> find the token index it targets
    lbl_target_idx = []
    for lbl in labels:
        off = lbl - 2
        idx = off_to_idx.get(off, -1)
        lbl_target_idx.append(idx)  # -1 = unresolved (end of script)

    # build new token stream
    new_tokens = []          # (op, payload_bytes_or_None, class)
    idx_map = {}             # old token idx -> new token idx
    errors = []
    for i, (off, op, ln, s, raw) in enumerate(tokens):
        pc_op = opmap.get(op)
        if pc_op is None:
            errors.append(f"op 0x{op:02X} at token {i} unmapped")
            if strict:
                raise ValueError(f"unmapped PS2 opcode 0x{op:02X} (token {i}); add to map or use --no-strict")
            pc_op = op
        cls1 = classify(op, "ps2")
        cls2 = classify(pc_op, "pc")
        if cls1 == "u8x2" and cls2 == "u8x2":
            new_tokens.append((pc_op, raw[1:3]))
        elif cls1 == "u16x4" and cls2 == "u16x4":
            new_tokens.append((pc_op, raw[1:9]))
        elif s is not None:
            # string ops: PS2 str/encstr -> PC str/encstr
            if cls1 == "encstr" and cls2 == "encstr":
                new_tokens.append((pc_op, s))
            elif cls1 == "encstr" and cls2 == "str":
                new_tokens.append((pc_op, dc2_mes.decrypt(s)))
            elif cls1 == "str" and cls2 == "encstr":
                new_tokens.append((pc_op, dc2_mes.encrypt(s)))
            else:
                new_tokens.append((pc_op, s))
        elif cls1 == "u8str" and cls2 == "u8str":
            new_tokens.append((pc_op, raw[1:]))     # arg + str + NUL handled at build
        elif cls1 == "u8str" and cls2 == "str":
            new_tokens.append((pc_op, raw[2:]))     # drop the arg byte
        elif cls1 == "str" and cls2 == "u8str":
            new_tokens.append((pc_op, b"\x00" + raw[1:]))  # add arg 0
        else:
            # class mismatch without payload knowledge — keep raw payload as-is
            errors.append(f"token {i}: class {cls1}->(0x{pc_op:02X}) {cls2} payload fallback")
            new_tokens.append((pc_op, raw[1:]))
        idx_map[i] = len(new_tokens) - 1

    # assemble bytecode
    bc = bytearray()
    new_offsets = []
    for op, payload in new_tokens:
        new_offsets.append(len(bc))
        bc.append(op)
        if payload is not None:
            bc += payload
            if payload[-1:] != b"\x00":
                bc.append(0)     # ensure NUL for string-ish ops
    # wait: for u8x2/u16x4 payloads we must NOT append NUL. fix by class:
    # (rebuild properly below)
    # -- redo cleanly:
    bc = bytearray()
    new_offsets = []
    for i, (op, payload) in enumerate(new_tokens):
        cls1 = classify(tokens[i][1], "ps2")
        new_offsets.append(len(bc))
        bc.append(op)
        if cls1 in ("u8x2",):
            bc += payload                    # exactly 2 bytes
        elif cls1 == "u16x4":
            bc += payload                    # exactly 8 bytes
        elif cls1 == "u8str":
            # payload = arg + string; ensure NUL
            if not payload.endswith(b"\x00"):
                bc += payload + b"\x00"
            else:
                bc += payload
        else:
            # str / encstr: payload = string, ensure NUL
            if payload.endswith(b"\x00"):
                bc += payload
            else:
                bc += payload + b"\x00"

    # recompute labels: same token index, new offset + 2
    new_labels = []
    for idx in lbl_target_idx:
        if 0 <= idx < len(new_offsets):
            new_labels.append(new_offsets[idx] + 2)
        else:
            new_labels.append(len(bc) + 2)   # end-of-script fallback

    out = bytearray(struct.pack("<i", label_count))
    for lbl in new_labels:
        out += struct.pack("<i", lbl)
    out += struct.pack("<H", dc2_pcmes.MES_VERSION)
    out += bc
    return bytes(out), errors, len(tokens), len(new_tokens)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--map", default=os.path.join(os.path.dirname(__file__), "opcode_map2.json"))
    ap.add_argument("--no-strict", action="store_true")
    a = ap.parse_args()
    opmap = load_map(a.map)
    blob = open(a.src, "rb").read()
    out, errors, n1, n2 = transcode(blob, opmap, strict=not a.no_strict)
    open(a.dst, "wb").write(out)
    print(f"transcoded {a.src} -> {a.dst}: {n1} PS2 tokens -> {n2} PC tokens")
    if errors:
        print(f"{len(errors)} notes:")
        for e in errors[:10]:
            print("  ", e)
    # sanity: parse with PC parser
    try:
        dc2_pcmes.parse_mes(out)
        print("PC parse: OK")
    except Exception as e:
        print(f"PC parse: FAILED: {e}")


if __name__ == "__main__":
    main()