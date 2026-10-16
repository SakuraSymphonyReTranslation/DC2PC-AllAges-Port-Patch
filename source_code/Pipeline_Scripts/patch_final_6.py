#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_final_6.py — Patch the final 6 remaining dialogue lines in ALLAGES/AdvData/MES/
to achieve 100.0% Indonesian translation coverage.
"""

import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dc2_pcmes

MES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ALLAGES", "AdvData", "MES")

TRANSLATIONS_FINAL_6 = {
    ("fst_1217_a3_cmn.mes", 168): "Meski itu murni sebuah kecelakaan, tanpa memberiku kesempatan untuk membela diri sedikit pun, dia langsung melayangkan tamparan keras sekuat tenaga.",
    ("fst_1217_c2_cmn.mes", 14): "「Sampai-sampai orang hampir tidak bisa membedakannya dari manusia biasa」",
    ("fst_1217_c2_cmn.mes", 67): "「Fakta bahwa yang mengaktifkan Amakase adalah Sakurai-kun... mungkin itu sudah menjadi takdir pertemuan kalian」",
    ("fst_1220_c1_yme.mes", 86): "Meski kamu bilang begitu juga, ya~",
    ("fst_1220_c1_yme.mes", 87): "『Jigoku-don』 itu hidangan mengerikan yang dibuat dengan merebus cabai habanero yang konon paling pedas di dunia, bersama doubanjiang, minyak cabai, dan cabai hijau selama tiga hari tiga malam──",
    ("fst_1222_c1_e3_2.mes", 10): "「Sakurai-kun, kamu t~idak melihat apa-apa, kan?\n{oke/OK}?」",
    ("fst_1223_e1_snb.mes", 296): "{・・/Sesuatu} yang melilit lenganku adalah sebuah rantai berkilau berwarna {kelabu/abu-abu kusam} dengan pemberat yang berat......bukan, itu adalah sebuah kusarigama.",
}


def wrap_text(text: str, width: int = 54) -> str:
    if "\n" in text:
        parts = text.split("\n")
        return "\n".join(wrap_text(p, width) for p in parts)

    words = text.split(" ")
    lines = []
    curr = ""
    for w in words:
        if not curr:
            curr = w
        elif len(curr) + 1 + len(w) <= width:
            curr += " " + w
        else:
            lines.append(curr)
            curr = w
    if curr:
        lines.append(curr)
    return "\n".join(lines)


def sanitize_for_circus(text: str) -> str:
    return text.replace(" ", "\u3000").replace("$", "＄")


def main():
    print("=== Patching Final Remaining Lines ===")
    from collections import defaultdict
    by_file = defaultdict(list)
    for (fn, idx), tr in TRANSLATIONS_FINAL_6.items():
        by_file[fn].append((idx, tr))

    total_patched = 0
    for fname, edits in by_file.items():
        mes_path = os.path.join(MES_DIR, fname)
        if not os.path.exists(mes_path):
            print(f"Error: {fname} not found!")
            continue

        blob = open(mes_path, "rb").read()
        hdr, labels, tokens = dc2_pcmes.parse_mes(blob)
        dialogue = dc2_pcmes.extract_dialogue(blob)

        reps = {}
        for (idx, tr_text) in edits:
            if idx < len(dialogue):
                entry = dialogue[idx]
                wrapped = wrap_text(tr_text, width=54)
                safe = sanitize_for_circus(wrapped)
                raw = safe.encode("cp932", errors="replace")
                if entry["type"] in ("dialogue", "choice"):
                    reps[entry["message_offset"]] = dc2_pcmes.encrypt(raw)
                else:
                    reps[entry["message_offset"]] = raw
                total_patched += 1
                print(f"Patched {fname} [{idx}] -> {tr_text[:40]}...")

        if reps:
            rebuilt = dc2_pcmes.rebuild_mes(hdr, labels, tokens, reps)
            _h2, _l2, _t2 = dc2_pcmes.parse_mes(rebuilt)
            with open(mes_path, "wb") as fp:
                fp.write(rebuilt)

    print(f"Done! Total patched: {total_patched}")


if __name__ == "__main__":
    main()
