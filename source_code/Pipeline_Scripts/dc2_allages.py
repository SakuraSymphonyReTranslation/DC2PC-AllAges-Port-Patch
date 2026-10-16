#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dc2_allages.py — Phase B: build the all-ages PC script set from DC2PC + DC2PS.

Strategies (per script):
  A) Normal scripts (1,515 shared, 1,405 with identical dialogue counts):
     apply the PS2 all-ages wording line-by-line via dc2_pcmes rebuild.
  B) The 33 h-scene scripts: PC and PS2 scenes differ structurally.  Apply
     *command-level* edits to the PC script instead:
       - remap every PC-only (18+) CG reference to the shared CG the PS2 scene
         uses at the corresponding story point (cg_map.json),
       - replace aligned dialogue text with the PS2 all-ages wording,
       - optionally strip voice refs for the h-scene (all-ages re-records),
     keeping the PC token stream, labels and engine housekeeping intact.

Commands:
  status    - summarize the port state
  wording   - apply the all-ages wording (aligned-line) patches
  scenes    - apply the 33 h-scene CG-swap patches
  build     - wording + scenes, write output tree

Usage:
  python tools/dc2_allages.py build --pc DC2PC/AdvData --out ALLAGES
"""

import argparse
import json
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dc2_mes      # noqa: E402  (PS2)
import dc2_pcmes    # noqa: E402  (PC)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def norm_text(s: str) -> str:
    """Aggressive normalization used to decide 'same line' (punctuation-only diff)."""
    s = s.replace("\u3000", "").replace("\n", "").replace(" ", "")
    s = s.replace("~", "\u301C").replace("\uFF5E", "\u301C")
    s = s.replace("!", "\uFF01").replace("?", "\uFF1F")
    s = s.replace("\u2212", "-").replace("\u2014", "-")
    return s


def load_json(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return json.load(f)


def collect_wording_edits():
    """allages_wording_diffs.json -> {script_lower: {line_idx: ps2_msg}} for REAL diffs."""
    diffs = load_json("allages_wording_diffs.json")
    per = {}
    for x in diffs:
        if norm_text(x["pc_msg"]) == norm_text(x["ps2_msg"]):
            continue  # punctuation/wrap-only
        per.setdefault(x["script"].lower(), {})[x["line_idx"]] = x["ps2_msg"]
    return per


def patch_script_wording(blob: bytes, line_edits: dict):
    """Apply {line_idx: new_text} to a PC script; returns (new_bytes, n_applied)."""
    hdr, labels, tokens = dc2_pcmes.parse_mes(blob)
    lines = dc2_pcmes.extract_dialogue(blob)
    reps = {}
    for li, new_text in line_edits.items():
        if li >= len(lines):
            continue
        off = lines[li].get("message_offset")
        if off is None:
            continue
        raw = new_text.replace("\r", "").encode("cp932", errors="replace")
        reps[off] = dc2_pcmes.encrypt(raw)
    if not reps:
        return blob, 0
    return dc2_pcmes.rebuild_mes(hdr, labels, tokens, reps), len(reps)


def patch_script_cg(blob: bytes, cg_subs: dict):
    """Replace asset-name strings in PC string tokens: {'EV_MHR15A': 'EV_MHR01A', ...}.

    PC asset refs are lowercase; PS2 CG names uppercase.  We rewrite the string
    payloads of ops whose decoded text contains a target name.
    """
    hdr, labels, tokens = dc2_pcmes.parse_mes(blob)
    subs = {k.lower(): v.lower() for k, v in cg_subs.items()}
    reps = {}
    for (off, op, ln, s, raw) in tokens:
        if s is None:
            continue
        if dc2_pcmes.ENCSTR_LO <= op <= dc2_pcmes.ENCSTR_HI:
            plain = dc2_pcmes.decrypt(s)
            was_enc = True
        else:
            plain = s
            was_enc = False
        try:
            text = plain.decode("cp932")
        except Exception:
            continue
        low = text.lower()
        hit = None
        for k, v in subs.items():
            if k in low:
                hit = (k, v)
                break
        if not hit:
            continue
        k, v = hit
        # replace whole token only when the token IS the ref (typical: 'ev\\ev_x' or 'ev_x')
        new_text = v if low.strip("\\0") == k or low == k else text.replace(k, v)
        raw_new = new_text.encode("cp932", errors="replace")
        reps[off] = dc2_pcmes.encrypt(raw_new) if was_enc else raw_new
    if not reps:
        return blob, 0
    return dc2_pcmes.rebuild_mes(hdr, labels, tokens, reps), len(reps)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["status", "wording", "scenes", "build"])
    ap.add_argument("--pc", default=os.path.join("DC2PC", "AdvData"))
    ap.add_argument("--out", default="ALLAGES")
    a = ap.parse_args()

    pc_mes = os.path.join(a.pc, "MES")

    if a.cmd == "status":
        edits = collect_wording_edits()
        n = sum(len(v) for v in edits.values())
        print(f"real wording edits: {n} lines across {len(edits)} scripts")
        return

    if a.cmd == "wording":
        edits = collect_wording_edits()
        outdir = os.path.join(a.out, "MES")
        os.makedirs(outdir, exist_ok=True)
        applied = 0
        for fname in sorted(os.listdir(pc_mes)):
            key = fname.lower()
            blob = open(os.path.join(pc_mes, fname), "rb").read()
            if key in edits:
                blob, n = patch_script_wording(blob, edits[key])
                applied += n
            with open(os.path.join(outdir, fname), "wb") as f:
                f.write(blob)
        print(f"applied {applied} all-ages wording edits -> {outdir}")
        return

    if a.cmd == "scenes":
        cg_map = load_json("cg_map.json")
        # default substitution: PC-only CG -> the shared CG with same prefix family
        # (story-equivalent art); specific map can be dropped in later.
        shared = cg_map["shared"]
        subs = {}
        for name in cg_map["pc_only"]:
            fam = name[:6]          # e.g. 'EV_MHR'
            cands = [c for c in shared if c.startswith(fam)]
            subs[name] = cands[0] if cands else name
        outdir = os.path.join(a.out, "MES")
        os.makedirs(outdir, exist_ok=True)
        os.makedirs(pc_mes, exist_ok=True)
        total = 0
        for fname in sorted(os.listdir(pc_mes)):
            blob = open(os.path.join(pc_mes, fname), "rb").read()
            used = {k: v for k, v in subs.items() if k.encode() in blob or k.lower().encode() in blob}
            if used:
                blob, n = patch_script_cg(blob, used)
                total += n
            with open(os.path.join(outdir, fname), "wb") as f:
                f.write(blob)
        print(f"applied {total} CG substitutions -> {outdir}")
        return

    if a.cmd == "build":
        a.out = a.out
        print("== wording ==")
        wording_main(a)
        print("== scenes ==")
        scenes_main(a)
        return


def wording_main(a):
    edits = collect_wording_edits()
    outdir = os.path.join(a.out, "MES")
    os.makedirs(outdir, exist_ok=True)
    applied = 0
    for fname in sorted(os.listdir(pc_mes_dir(a))):
        key = fname.lower()
        blob = open(os.path.join(pc_mes_dir(a), fname), "rb").read()
        if key in edits:
            blob, n = patch_script_wording(blob, edits[key])
            applied += n
        with open(os.path.join(outdir, fname), "wb") as f:
            f.write(blob)
    print(f"applied {applied} wording edits")


def scenes_main(a):
    cg_map = load_json("cg_map.json")
    shared = cg_map["shared"]
    subs = {}
    for name in cg_map["pc_only"]:
        fam = name[:6]
        cands = [c for c in shared if c.startswith(fam)]
        subs[name] = cands[0] if cands else name
    outdir = os.path.join(a.out, "MES")
    total = 0
    for fname in sorted(os.listdir(pc_mes_dir(a))):
        blob = open(os.path.join(pc_mes_dir(a), fname), "rb").read()
        used = {k: v for k, v in subs.items()
                if k.lower().encode() in blob.lower()}
        if used:
            blob, n = patch_script_cg(blob, used)
            total += n
        with open(os.path.join(outdir, fname), "wb") as f:
            f.write(blob)
    print(f"applied {total} CG substitutions")


def pc_mes_dir(a):
    return os.path.join(a.pc, "MES")


if __name__ == "__main__":
    main()