#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_all_sce_thumbnails.py — Sanitize all 13 Scene Viewer (回想) thumbnail chips (sce_*_chip.CRX)
by replacing all 33 explicit 18+ thumbnails with official clean All-Ages CG thumbnails.
"""

import os
import sys
import struct
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dc2_pcmes
import dc2_crx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_GRP = os.path.join(ROOT, "DC2PC", "AdvData", "GRP", "SYSTEM")
OUT_GRP = os.path.join(ROOT, "ALLAGES", "AdvData", "GRP", "SYSTEM")
BG_GRP = os.path.join(ROOT, "ALLAGES", "AdvData", "GRP", "bg")
MES_DIR = os.path.join(ROOT, "DC2PC", "AdvData", "MES")

# Exact mapping of all 33 scenes and their safe All-Ages replacement CGs
REPLACEMENTS = {
    # Otome
    ("otome", "sce94", "ind_0401_f1_otm"): "ev_otm22a.CRX",
    # Yume
    ("yume", "sce67", "ind_0120_f3_yme"): "ev_yme19a.CRX",
    ("yume", "sce71", "ind_0121_f2_yme"): "ev_yme21a.CRX",
    ("yume", "sce82", "ind_0128_a1_yme"): "ev_yme20a.CRX",
    # Nanaka
    ("nanaka", "sce59", "ind_0116_f1_nnk"): "ev_nnk21a.CRX",
    ("nanaka", "sce84", "ind_0127_f1_nnk"): "iv_nnk09m.CRX",
    # Minatu
    ("minatu", "sce56", "ind_0116_f1_mnt"): "ev_mnt19a.CRX",
    ("minatu", "sce71", "ind_0120_f1_mnt"): "ev_mnt21a.CRX",
    # Anzu
    ("anzu", "sce83", "ind_0129_f2_anz"): "ev_anz22a.CRX",
    # Koko
    ("koko", "sce94", "ind_0127_f3_kko"): "ev_kko20a.CRX",
    # Aisia
    ("aisia", "sce27", "mdl_1229_b1_ais"): "ev_ais01a.CRX",
    ("aisia", "sce55", "ind_0116_d1_ais"): "ev_ais01a.CRX",
    ("aisia", "sce61", "ind_0121_e2_ais"): "ev_ais09a.CRX",
    # Erika
    ("erika", "sce66", "ind_0118_f2_erk"): "ev_erk09a.CRX",
    ("erika", "sce76", "ind_0120_f2_erk"): "ev_erk01a.CRX",
    # Akane
    ("akane", "sce28", "mdl_1230_e1_cm51"): "ev_akn01a.CRX",
    ("akane", "sce35", "mdl_0101_d11_akn"): "ev_akn01a.CRX",
    ("akane", "sce53", "ind_0115_f2_akn"): "ev_akn01a.CRX",
    ("akane", "sce85", "ind_0211_f1_akn"): "ev_akn01a.CRX",
    # Maya
    ("maya", "sce23", "mdl_1230_e1_cm52"): "ev_mya01a.CRX",
    ("maya", "sce63", "ind_0120_f3_mya"): "ev_mya01a.CRX",
    ("maya", "sce79", "ind_0124_f1_mya"): "ev_mya01a.CRX",
    # Mayuki
    ("mayuki", "sce60", "ind_0116_b1_myk"): "ev_myk21a.CRX",
    ("mayuki", "sce82", "ind_0122_f3_myk"): "ev_myk01a.CRX",
    ("mayuki", "sce96", "ind_0128_f2_myk"): "ev_myk01a.CRX",
    # Mahiru
    ("mahiru", "sce15", "mdl_1225_f2_mhr"): "ev_mhr01a.CRX",
    ("mahiru", "sce19", "mdl_1226_f2_mhr"): "ev_mhr01a.CRX",
    ("mahiru", "sce23", "mdl_1227_f1_mhr"): "ev_mhr01a.CRX",
    ("mahiru", "sce28", "mdl_1229_f1_mhr"): "ev_mhr01a.CRX",
    ("mahiru", "sce42", "ind_0101_f1_mhr"): "ev_mhr01a.CRX",
    ("mahiru", "sce48", "ind_0102_f1_mhr"): "ev_mhr06a.CRX",
    # Other
    ("other", "sce357", "fst_1224_f1_snb"): "ev_snb01a.CRX",
    ("other", "sce396", "ind_0110_e1_rno"): "ev_rno01a.CRX",
}

CHARS = [
    "otome", "yume", "nanaka", "minatu", "anzu", "koko",
    "aisia", "erika", "akane", "maya", "mayuki", "mahiru", "other"
]

def load_cg(cg_name):
    # Case insensitive lookup in BG_GRP
    for f in os.listdir(BG_GRP):
        if f.lower() == cg_name.lower():
            p = os.path.join(BG_GRP, f)
            with open(p, "rb") as fp:
                return dc2_crx.decode_crx(fp.read())
    raise FileNotFoundError(f"CG {cg_name} not found in {BG_GRP}")

def main():
    print("=== Sanitizing all 13 Scene Viewer (回想) thumbnail chips ===")
    os.makedirs(OUT_GRP, exist_ok=True)
    
    # Cache decoded CG thumbnails (68x52)
    thumb_cache = {}
    
    total_replaced = 0
    
    for char in CHARS:
        chip_filename = f"sce_{char}_chip.CRX"
        src_chip_path = os.path.join(SRC_GRP, chip_filename)
        out_chip_path = os.path.join(OUT_GRP, chip_filename)
        
        # Read and decode original chip
        with open(src_chip_path, "rb") as fp:
            chip_img = dc2_crx.decode_crx(fp.read())
            
        # Parse mes to find exact tile coordinates for this character
        mes_path = os.path.join(MES_DIR, f"sce_{char}.mes")
        with open(mes_path, "rb") as fp:
            hdr, labels, tokens = dc2_pcmes.parse_mes(fp.read())
            
        label_to_target = {}
        for i, t in enumerate(tokens):
            s = t[3].decode("cp932", errors="replace") if t[3] else ""
            if t[1] == 0x35 and s.startswith("sce"):
                for j in range(i, min(len(tokens), i + 20)):
                    if tokens[j][1] == 0x2E:
                        label_to_target[s] = tokens[j][3].decode("cp932", errors="replace")
                        break
                        
        char_replacements = 0
        for i, t in enumerate(tokens):
            s = t[3].decode("cp932", errors="replace") if t[3] else ""
            if t[1] == 0x42 and s.startswith("sce"):
                target = label_to_target.get(s, "")
                key = (char, s, target)
                if key in REPLACEMENTS:
                    cg_name = REPLACEMENTS[key]
                    p57 = struct.unpack("<4h", tokens[i-2][4][1:])
                    flag, comp, x1, y1 = p57
                    
                    # Prepare thumb
                    if cg_name not in thumb_cache:
                        cg_img = load_cg(cg_name)
                        thumb = cg_img.resize((68, 52), Image.Resampling.LANCZOS)
                        thumb_cache[cg_name] = thumb
                    else:
                        thumb = thumb_cache[cg_name]
                        
                    # Paste over explicit tile
                    chip_img.paste(thumb, (x1, y1))
                    char_replacements += 1
                    total_replaced += 1
                    print(f"  [{char:8}] {s:6} ({target:18}) at ({x1:4}, {y1:3}) -> replaced with {cg_name}")
                    
        # Encode modified chip and write to ALLAGES/AdvData/GRP/SYSTEM/
        enc_bytes = dc2_crx.encode_crx(chip_img)
        with open(out_chip_path, "wb") as fp:
            fp.write(enc_bytes)
            
        print(f"[{char:8}] Saved {chip_filename} ({char_replacements} tiles sanitized, size: {len(enc_bytes):,} bytes)")

    print(f"\nSUCCESS: All {total_replaced} explicit thumbnails sanitized across all 13 characters!")

if __name__ == "__main__":
    main()
