#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild_all_scripts.py — Build the complete All-Ages MES script set for D.C.II P.C.

Combines:
  1. The 13 re-engineered All-Ages CG viewer scripts (cg_*.mes).
  2. The 25 official PS2 All-Ages replacement scenes transcoded from PS2 MES.DAT.
  3. The 8 skipped PC-only H-scenes replaced by immediate-jump stubs and their callers redirected.
  4. All ~1,512 regular story scripts restored from pristine DC2PC, with PS2 All-Ages wording
     patches applied (all voices 100% preserved).
"""

import os
import sys
import json
import struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dc2_mes
import dc2_pcmes
import dc2_transcode
import dc2_allages

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PC_MES_DIR = os.path.join(ROOT, "DC2PC", "AdvData", "MES")
OUT_MES_DIR = os.path.join(ROOT, "ALLAGES", "AdvData", "MES")
PS2_MES_DAT = os.path.join(ROOT, "PS2_extracted", "DAT", "MES.DAT")
OPCODE_MAP_FILE = os.path.join(ROOT, "opcode_map_final.json")
WORDING_DIFFS_FILE = os.path.join(ROOT, "allages_wording_diffs.json")

# The 25 H-scenes that have official PS2 All-Ages replacement scenes
MATCHED_25 = {
    'fst_1224_f1_snb.mes': 'FST_1224_F1_SNB.MES',
    'ind_0101_f1_mhr.mes': 'IND_0101_F1_MHR.MES',
    'ind_0102_f1_mhr.mes': 'IND_0102_F1_MHR.MES',
    'ind_0110_e1_rno.mes': 'IND_0110_E1_RNO.MES',
    'ind_0116_b1_myk.mes': 'IND_0116_B1_MYK.MES',
    'ind_0116_d1_ais.mes': 'IND_0116_D1_AIS.MES',
    'ind_0116_f1_mnt.mes': 'IND_0116_F1_MNT.MES',
    'ind_0116_f1_nnk.mes': 'IND_0116_F1_NNK.MES',
    'ind_0118_f2_erk.mes': 'IND_0118_F2_ERK.MES',
    'ind_0120_f1_mnt.mes': 'IND_0120_F1_MNT.MES',
    'ind_0120_f2_erk.mes': 'IND_0120_F2_ERK.MES',
    'ind_0120_f3_yme.mes': 'IND_0120_F3_YME.MES',
    'ind_0121_f2_yme.mes': 'IND_0121_F2_YME.MES',
    'ind_0127_f1_nnk.mes': 'IND_0127_F1_NNK.MES',
    'ind_0127_f3_kko.mes': 'IND_0127_F3_KKO.MES',
    'ind_0128_a1_yme.mes': 'IND_0128_A1_YME.MES',
    'ind_0129_f2_anz.mes': 'IND_0129_F2_ANZ.MES',
    'ind_0401_f1_otm.mes': 'IND_0401_F1_OTM.MES',
    'mdl_0101_d11_akn.mes': 'MDL_0101_D11_AKN.MES',
    'mdl_1225_f2_mhr.mes': 'MDL_1225_F2_MHR.MES',
    'mdl_1227_f1_mhr.mes': 'MDL_1227_F1_MHR.MES',
    'mdl_1229_b1_ais.mes': 'MDL_1229_B1_AIS.MES',
    'mdl_1229_f1_mhr.mes': 'MDL_1229_F1_MHR.MES',
    'mdl_1230_e1_cm51.mes': 'MDL_1230_E1_CM51.MES',
    'mdl_1230_e1_cm52.mes': 'MDL_1230_E1_CM52.MES',
}

# The 8 skipped H-scenes and their destinations
SKIPPED_8 = {
    'ind_0115_f2_akn.mes': 'ind_0116_a1_akn',
    'ind_0120_f3_mya.mes': 'ind_0121_a1_mya',
    'ind_0121_e2_ais.mes': 'ind_0121_f1_ais',
    'ind_0122_f3_myk.mes': 'ind_0123_b1_myk',
    'ind_0124_f1_mya.mes': 'ind_0125_a1_mya',
    'ind_0128_f2_myk.mes': 'ind_0129_b1_myk',
    'ind_0211_f1_akn.mes': 'ind_0212_a1_akn',
    'mdl_1226_f2_mhr.mes': 'mdl_1227_b1_mhr',
}

# Their callers and the replacement jump targets
CALLER_REDIRECTS = {
    'ind_0115_f1_akn.mes': (b'ind_0115_f2_akn', b'ind_0116_a1_akn'),
    'ind_0120_f2_mya.mes': (b'ind_0120_f3_mya', b'ind_0121_a1_mya'),
    'ind_0121_e1_ais.mes': (b'ind_0121_e2_ais', b'ind_0121_f1_ais'),
    'ind_0122_f2_myk.mes': (b'ind_0122_f3_myk', b'ind_0123_b1_myk'),
    'ind_0124_e2_mya.mes': (b'ind_0124_f1_mya', b'ind_0125_a1_mya'),
    'ind_0128_f1_myk.mes': (b'ind_0128_f2_myk', b'ind_0129_b1_myk'),
    'ind_0211_b1_akn.mes': (b'ind_0211_f1_akn', b'ind_0212_a1_akn'),
    'mdl_1226_f1_mhr.mes': (b'mdl_1226_f2_mhr', b'mdl_1227_b1_mhr'),
}


def make_jump_stub(target_script: str) -> bytes:
    """Create a minimal, valid PC MES bytecode that immediately jumps to target_script."""
    target_bytes = target_script.encode("cp932")
    bc = bytearray()
    bc += b'\x64\x00\x00\x00\x00\x00\x00\x00\x00'       # header op 0x64
    bc += b'\x2e\x01' + target_bytes + b'\x00'          # jump op 0x2E
    bc += b'\x00\x00\x00'                              # halt op 0x00

    label_count = 1
    labels = [2]
    out = bytearray(struct.pack('<i', label_count))
    out += struct.pack('<i', labels[0])
    out += struct.pack('<H', dc2_pcmes.MES_VERSION)
    out += bc
    return bytes(out)


def patch_caller_script(blob: bytes, old_target: bytes, new_target: bytes) -> bytes:
    """Rewrite opcode 0x2E jump target in caller script."""
    hdr, labels, tokens = dc2_pcmes.parse_mes(blob)
    reps = {}
    for off, op, ln, s, raw in tokens:
        if s == old_target:
            # op 0x2E: raw starts with [op][arg], so replace with [arg] + new_target
            reps[off] = raw[1:2] + new_target
    if reps:
        return dc2_pcmes.rebuild_mes(hdr, labels, tokens, reps)
    return blob


def postprocess_transcoded_script(pc_bytes: bytes) -> bytes:
    """Clean up asset references in transcoded PS2 script (normalize '+' suffixes, lowercase)."""
    hdr, labels, tokens = dc2_pcmes.parse_mes(pc_bytes)
    reps = {}
    for off, op, ln, s, raw in tokens:
        if s and any(s.upper().startswith(p) for p in [b'BG\\', b'EV\\', b'IV\\']):
            text = s.decode('cp932', errors='ignore').strip('\x00')
            # normalize '+' at the end of background references
            if text.endswith('+'):
                new_text = text[:-1]
                reps[off] = new_text.encode('cp932')
    if reps:
        return dc2_pcmes.rebuild_mes(hdr, labels, tokens, reps)
    return pc_bytes


def main():
    print("=== Step 1: Preserving existing CG Viewer scripts ===")
    cg_scripts = {}
    for fname in os.listdir(OUT_MES_DIR):
        if fname.lower().startswith("cg_") and fname.lower().endswith(".mes"):
            cg_scripts[fname.lower()] = open(os.path.join(OUT_MES_DIR, fname), "rb").read()
    print(f"Preserved {len(cg_scripts)} CG viewer scripts.")

    print("\n=== Step 2: Loading PS2 MES.DAT for transcoding ===")
    with open(PS2_MES_DAT, "rb") as f:
        ps2_files = {e[0].upper(): e[3] for e in dc2_mes.parse_mes_dat(f.read())}
    print(f"Loaded {len(ps2_files)} PS2 scripts.")

    opmap = dc2_transcode.load_map(OPCODE_MAP_FILE)

    print("\n=== Step 3: Loading All-Ages wording diffs ===")
    wording_edits = dc2_allages.collect_wording_edits()
    print(f"Loaded wording edits for {len(wording_edits)} scripts.")

    print("\n=== Step 4: Rebuilding ALL MES scripts ===")
    os.makedirs(OUT_MES_DIR, exist_ok=True)
    all_pc_files = sorted([f for f in os.listdir(PC_MES_DIR) if f.lower().endswith(".mes")])
    print(f"Total scripts in DC2PC: {len(all_pc_files)}")

    stats = {
        "cg_viewer": 0,
        "transcoded_ps2": 0,
        "skipped_stubs": 0,
        "callers_redirected": 0,
        "wording_patched": 0,
        "regular_clean": 0,
    }

    for fname in all_pc_files:
        key = fname.lower()
        out_path = os.path.join(OUT_MES_DIR, fname)

        # 1. CG Viewer scripts
        if key in cg_scripts:
            with open(out_path, "wb") as f:
                f.write(cg_scripts[key])
            stats["cg_viewer"] += 1
            continue

        # 2. The 25 PS2 replacement scenes
        if key in MATCHED_25:
            ps2_name = MATCHED_25[key]
            ps2_blob = ps2_files[ps2_name]
            pc_bytes, errors, n1, n2 = dc2_transcode.transcode(ps2_blob, opmap, strict=True)
            pc_bytes = postprocess_transcoded_script(pc_bytes)
            with open(out_path, "wb") as f:
                f.write(pc_bytes)
            stats["transcoded_ps2"] += 1
            continue

        # 3. The 8 skipped H-scenes (write stub)
        if key in SKIPPED_8:
            stub_bytes = make_jump_stub(SKIPPED_8[key])
            with open(out_path, "wb") as f:
                f.write(stub_bytes)
            stats["skipped_stubs"] += 1
            continue

        # 4. Pristine PC scripts (regular story scripts)
        pc_blob = open(os.path.join(PC_MES_DIR, fname), "rb").read()

        # Apply wording edit if available
        if key in wording_edits:
            pc_blob, n = dc2_allages.patch_script_wording(pc_blob, wording_edits[key])
            stats["wording_patched"] += 1
        else:
            stats["regular_clean"] += 1

        # Apply caller redirect if this is one of the 8 callers
        if key in CALLER_REDIRECTS:
            old_tgt, new_tgt = CALLER_REDIRECTS[key]
            pc_blob = patch_caller_script(pc_blob, old_tgt, new_tgt)
            stats["callers_redirected"] += 1

        with open(out_path, "wb") as f:
            f.write(pc_blob)

    print("\nRebuild Summary:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print("\n=== Step 5: Verification ===")
    parse_ok = 0
    parse_fail = 0
    total_voices = 0
    pc_total_voices = 0

    cg_map = json.load(open(os.path.join(ROOT, "cg_map.json"), encoding="utf-8"))
    pc_only_set = set(x.upper() for x in cg_map["pc_only"])
    leaked_18_cg = []

    for fname in sorted(os.listdir(OUT_MES_DIR)):
        if not fname.lower().endswith(".mes"):
            continue
        p = os.path.join(OUT_MES_DIR, fname)
        data = open(p, "rb").read()
        total_voices += data.count(b"VOICE\\")

        pc_orig_p = os.path.join(PC_MES_DIR, fname)
        if os.path.exists(pc_orig_p):
            pc_total_voices += open(pc_orig_p, "rb").read().count(b"VOICE\\")

        try:
            hdr, labels, tokens = dc2_pcmes.parse_mes(data)
            parse_ok += 1
            for off, op, ln, s, raw in tokens:
                if s:
                    # check for 18+ CG
                    base = os.path.basename(s.decode("cp932", errors="ignore")).upper()
                    if base in pc_only_set:
                        leaked_18_cg.append((fname, base))
        except Exception as e:
            parse_fail += 1
            print(f"Parse error in {fname}: {e}")

    print(f"Parse verification: {parse_ok} OK, {parse_fail} FAIL")
    print(f"18+ CG references found: {len(leaked_18_cg)}")
    if leaked_18_cg:
        for item in leaked_18_cg[:10]:
            print(f"  Leaked in {item[0]}: {item[1]}")
    print(f"Total voice calls in ALLAGES: {total_voices} (PC had {pc_total_voices})")


if __name__ == "__main__":
    main()
