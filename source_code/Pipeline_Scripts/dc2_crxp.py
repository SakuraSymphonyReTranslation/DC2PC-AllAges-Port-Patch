#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dc2_crxp.py — PS2 CRXP image container decoder (D.C.II P.S., SLPM_669.22).

Reverse-engineered from the game ELF via IDA (2026-10-11), verified byte-exact
against real GRP.DAT data:

  sub_1054A0  Grp_Load(name, slot, async)    - resolves "BG\\X.GRP" via GRP.DAT
  sub_105AF8  Unpack ("alloc_packed")        - CRXP -> gbuf conversion
  sub_104AA8  alloc_gbuf                     - gbuf = [128B hdr][pixels]
  sub_123138  LZ77 unpacker (Circus LZSS, 8-bit flag cache, bit0 = literal)
  sub_140814  raw memcpy path

CRXP header (all u32 LE, file offset 0):
  0x00  "CRXP"
  0x04  width
  0x08  height
  0x0C  bpp selector: 0 = 24bpp, 1 = 32bpp (w3 in the ELF; see below)
  0x10  payload length (bytes; file size = 0x80 + payload)
  0x14..0x7F  zero padding

Payload (starts at file offset 0x80 — the game reads the blob from +0x80,
leaving 0x80 bytes of gbuf header above it):
  w3=1 (32bpp): LZ77-compressed, unpacked size = 4*w*h — straight BGRA rows
                (PS2 order R,G,B,A in memory per the game's GS upload path;
                we map to RGBA for PNG).
  w3=0 (24bpp): LZ77-compressed, unpacked size = 3*w*h (+ possibly alignment)
                — straight BGR rows, fully opaque.

Unpacker (sub_123138) — exact transcription, verified: BG 640x448 unpacks to
exactly 4*w*h; BST 704x564 to exactly 4*w*h (the +1536/+2176 palette paths in
the decompile belong to a different colmode branch (v20[5], always 0 in this
game's data) and are NOT used for w3=0/1).

Flag/bit mechanism: a 9-bit cache; >>1 each symbol; when bit8 drains, load a
new flag byte (cache = byte | 0xFF00). Bit0=1 -> literal byte. Bit0=0 ->
back-reference selected by the NEXT byte b:

  b < 0xC0, b & 0x80 :  disp = b & 0x1F (if 0 -> next byte); cnt = ((b>>5)&3)+2
  b < 0xC0, b == 0x7F:  4 bytes c0,c1,d0,d1: cnt = (c0|c1<<8)+2; disp = d0|d1<<8
  b < 0xC0, else     :  disp = b2 | (b3<<8) (2 bytes);  cnt = b + 4
  b >= 0xC0          :  disp = ((b&3)<<8) | next;       cnt = ((b>>2)&0xF)+4

Copy source = out_end - disp  (disp is a plain backward distance; disp=0 is
never produced in practice because cnt>=2 would self-feed the same position).

Usage:
  python tools/dc2_crxp.py list
  python tools/dc2_crxp.py decode "BG\\BG000_D_EC.GRP" out.png
  python tools/dc2_crxp.py all OUTDIR [--only BG]
"""

import argparse
import collections
import os
import struct
import sys
import zlib


# ---------------------------------------------------------------------------
# LZ77 unpacker — faithful transcription of sub_123138
# ---------------------------------------------------------------------------
def lz77_unpack(src: bytes, n: int) -> bytearray:
    """Fast unpacker (byte-identical to lz77_unpack_ref). Back-references use
    slice copies; overlapping runs use the LZ77 period-replication rule."""
    out = bytearray()
    cache = 0
    i = 0
    rem = n
    while rem > 0:
        cache >>= 1
        if not (cache & 0x100):
            cache = src[i] | 0xFF00
            i += 1
            rem -= 1
        if cache & 1:                       # literal
            out.append(src[i])
            i += 1
            rem -= 1
            continue
        if rem == 0:
            break
        b = src[i]
        i += 1
        rem -= 1
        if b < 0xC0:
            if b & 0x80:
                disp = b & 0x1F
                if disp == 0:
                    disp = src[i]
                    i += 1
                    rem -= 1
                cnt = ((b >> 5) & 3) + 2
            elif b == 0x7F:
                cnt = (src[i] | (src[i + 1] << 8)) + 2
                disp = src[i + 2] | (src[i + 3] << 8)
                i += 4
                rem -= 4
            else:
                disp = src[i] | (src[i + 1] << 8)
                i += 2
                rem -= 2
                cnt = b + 4
        else:
            disp = ((b & 3) << 8) | src[i]
            i += 1
            rem -= 1
            cnt = ((b >> 2) & 0xF) + 4
        pos = len(out) - disp
        if pos < 0:
            raise ValueError(f"LZ77: bad displacement {disp} at output {len(out)}")
        if cnt <= disp:
            out += out[pos:pos + cnt]
        else:
            seg = out[pos:]
            full = cnt // disp
            out += seg * full
            out += seg[:cnt - full * disp]
    return out


def lz77_unpack_ref(src: bytes, n: int) -> bytearray:
    """Reference (slow) transcription of sub_123138 — kept for verification."""
    out = bytearray()
    cache = 0
    i = 0
    remaining = n
    while remaining > 0:
        cache >>= 1
        if not (cache & 0x100):
            cache = src[i] | 0xFF00
            i += 1
            remaining -= 1
        if cache & 1:                       # literal
            out.append(src[i])
            i += 1
            remaining -= 1
            continue
        if remaining == 0:
            break
        b = src[i]
        i += 1
        remaining -= 1
        if b < 0xC0:
            if b & 0x80:
                disp = b & 0x1F
                if disp == 0:
                    disp = src[i]
                    i += 1
                    remaining -= 1
                cnt = ((b >> 5) & 3) + 2
            elif b == 0x7F:
                c0 = src[i]; i += 1
                c1 = src[i]; i += 1
                remaining -= 2
                cnt = (c0 | (c1 << 8)) + 2
                d0 = src[i]; i += 1
                d1 = src[i]; i += 1
                remaining -= 2
                disp = d0 | (d1 << 8)
            else:
                b2 = src[i]; i += 1
                remaining -= 1
                b3 = src[i]; i += 1
                remaining -= 1
                disp = b2 | (b3 << 8)
                cnt = b + 4
        else:
            disp = ((b & 3) << 8) | src[i]
            i += 1
            remaining -= 1
            cnt = ((b >> 2) & 0xF) + 4
        pos = len(out) - disp
        if pos < 0:
            raise ValueError(f"LZ77: bad displacement {disp} at output {len(out)}")
        for k in range(cnt):
            out.append(out[pos + k])
    return out


# ---------------------------------------------------------------------------
# CRXP container
# ---------------------------------------------------------------------------
def parse_crxp(blob: bytes):
    if blob[:4] != b"CRXP":
        raise ValueError(f"not CRXP: {blob[:4]!r}")
    w, h, bpp_sel, plen = struct.unpack_from("<IIII", blob, 4)
    return w, h, bpp_sel, plen


def crxp_to_rgba(blob: bytes):
    """Decode one CRXP entry -> (w, h, RGBA bytes)."""
    w, h, bpp_sel, plen = parse_crxp(blob)
    payload = blob[0x80:0x80 + plen]
    if len(payload) < plen:
        raise ValueError("payload truncated")

    unpacked = lz77_unpack(payload, plen)

    # Every CRXP in this game unpacks to 4*w*h straight RGBA (verified on BG,
    # BST and SYSTEM entries): R,G,B per pixel + BINARY alpha 0x80=opaque/0=clear.
    # (w3 differs 0/1 between files — transparency flag, irrelevant to decode.)
    expect = 4 * w * h
    if len(unpacked) < expect:
        raise ValueError(f"unpacked {len(unpacked)} < {expect}")
    out = bytearray(unpacked[:expect])
    for q in range(3, expect, 4):
        if out[q]:
            out[q] = 255              # normalize binary alpha 0x80 -> 255
    return w, h, bytes(out)


def write_png(path, w, h, rgba):
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
    raw = b"".join(b"\x00" + rgba[y * w * 4:(y + 1) * w * 4] for y in range(h))
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 6))
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def default_grp():
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in (
        os.path.join(here, "..", "..", "..", "PS2_extracted", "DAT", "GRP.DAT"),
        os.path.join(here, "..", "..", "PS2_extracted", "DAT", "GRP.DAT"),
        r"F:\Visual Novels\dc2pspc project\PS2_extracted\DAT\GRP.DAT",
    ):
        if os.path.exists(cand):
            return cand
    return "GRP.DAT"


def main():
    p = argparse.ArgumentParser(description="PS2 CRXP decoder for D.C.II P.S.")
    p.add_argument("cmd", choices=["list", "decode", "all"])
    p.add_argument("arg", nargs="?", default=None)
    p.add_argument("arg2", nargs="?", default=None)
    p.add_argument("--grp", default=default_grp())
    p.add_argument("--only", default=None, help="decode all: only this subdir prefix")
    a = p.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    import dc2_mes
    entries = {e[0]: e[3] for e in dc2_mes.parse_mes_dat(open(a.grp, "rb").read())}

    if a.cmd == "list":
        stats = collections.Counter()
        for name, blob in entries.items():
            if blob[:4] != b"CRXP":
                stats["other"] += 1
                continue
            w, h, cm, pl = parse_crxp(blob)
            stats[(cm, w, h)] += 1
        print("total CRXP:", sum(v for k, v in stats.items() if k != "other"))
        for k, v in sorted(stats.items(), key=lambda x: -x[1])[:25]:
            print(v, k)
        return

    if a.cmd == "decode":
        w, h, rgba = crxp_to_rgba(entries[a.arg])
        write_png(a.arg2, w, h, rgba)
        print(f"{a.arg}: {w}x{h} -> {a.arg2}")
        return

    if a.cmd == "all":
        outdir = a.arg or "crxp_png"
        os.makedirs(outdir, exist_ok=True)
        ok = fail = 0
        for name, blob in sorted(entries.items()):
            if blob[:4] != b"CRXP":
                continue
            if a.only and not name.startswith(a.only):
                continue
            safe = name.replace("\\", "__")
            try:
                w, h, rgba = crxp_to_rgba(blob)
                write_png(os.path.join(outdir, safe[:-4] + ".png"), w, h, rgba)
                ok += 1
            except Exception as e:
                print(f"FAIL {name}: {e}")
                fail += 1
        print(f"decoded {ok}, failed {fail} -> {outdir}")


if __name__ == "__main__":
    main()
