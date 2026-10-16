#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dc2_crx.py — D.C.II P.C. CRX Graphics Encoder & Decoder.

Supports:
  - 24bpp RGB and 32bpp RGBA images (Compression format 2, Mode 0).
  - Multi-candidate adaptive row filtering (Sub, Up, Up-Left) matching Circus format.
  - Image upscaling (e.g. PS2 640x448 -> PC 800x600).
  - Batch conversion of PNG/images to PC .CRX.

Usage:
------
  encode INPUT.png OUTPUT.crx [--resize 800 600]
  decode INPUT.crx OUTPUT.png
  batch_convert IN_DIR OUT_DIR [--resize 800 600]
"""

import sys
import os
import struct
import zlib
import io
import argparse
from PIL import Image

SIGNATURE = b"CRXG"


def decode_crx(data: bytes) -> Image.Image:
    """Decode a CRX file into a PIL Image."""
    if len(data) < 0x14 or data[:4] != SIGNATURE:
        raise ValueError("Invalid CRX signature")

    off_x, off_y, w, h = struct.unpack_from("<hhhh", data, 4)
    comp, flags, depth, mode = struct.unpack_from("<HHHH", data, 12)

    if comp != 2 and comp != 3:
        raise NotImplementedError(f"Unsupported compression {comp}")

    bpp = 24 if depth == 0 else (32 if depth == 1 else 8)
    if bpp == 8:
        raise NotImplementedError("Indexed 8bpp CRX decode not implemented")

    pixel_size = bpp // 8
    stride = (w * pixel_size + 3) & ~3
    src_stride = w * pixel_size

    decomp = zlib.decompress(data[0x14:])
    src = io.BytesIO(decomp)
    output = bytearray(h * stride)

    for y in range(h):
        ctl = src.read(1)[0]
        dst = y * stride
        prev_row = dst - stride
        if ctl == 0:
            output[dst:dst + pixel_size] = src.read(pixel_size)
            for x in range(pixel_size, src_stride):
                output[dst + x] = (src.read(1)[0] + output[dst + x - pixel_size]) & 0xFF
        elif ctl == 1:
            for x in range(src_stride):
                output[dst + x] = (src.read(1)[0] + output[prev_row + x]) & 0xFF
        elif ctl == 2:
            output[dst:dst + pixel_size] = src.read(pixel_size)
            for x in range(pixel_size, src_stride):
                output[dst + x] = (src.read(1)[0] + output[prev_row + x - pixel_size]) & 0xFF
        elif ctl == 3:
            for x in range(src_stride - pixel_size, 0, -1):
                output[dst] = (src.read(1)[0] + output[prev_row + pixel_size]) & 0xFF
                dst += 1
                prev_row += 1
            output[dst:dst + pixel_size] = src.read(pixel_size)
        elif ctl == 4:
            for i in range(pixel_size):
                cur_w = w
                val = src.read(1)[0]
                while cur_w > 0:
                    output[dst] = val
                    dst += pixel_size
                    cur_w -= 1
                    if cur_w == 0:
                        break
                    next_val = src.read(1)[0]
                    if val == next_val:
                        count = src.read(1)[0]
                        for j in range(count):
                            output[dst] = val
                            dst += pixel_size
                        cur_w -= count
                        if cur_w > 0:
                            val = src.read(1)[0]
                    else:
                        val = next_val
                dst -= src_stride - 1
        else:
            raise ValueError(f"Unknown row filter {ctl}")

    if bpp == 24:
        rgb = bytearray(w * h * 3)
        for y in range(h):
            row_in = y * stride
            row_out = y * w * 3
            for x in range(w):
                b = output[row_in + x * 3]
                g = output[row_in + x * 3 + 1]
                r = output[row_in + x * 3 + 2]
                rgb[row_out + x * 3] = r
                rgb[row_out + x * 3 + 1] = g
                rgb[row_out + x * 3 + 2] = b
        return Image.frombytes("RGB", (w, h), bytes(rgb))

    elif bpp == 32:
        alpha_flip = 0 if mode == 2 else 0xFF
        rgba = bytearray(w * h * 4)
        for y in range(h):
            row_in = y * stride
            row_out = y * w * 4
            for x in range(w):
                a = output[row_in + x * 4]
                b = output[row_in + x * 4 + 1]
                g = output[row_in + x * 4 + 2]
                r = output[row_in + x * 4 + 3]
                rgba[row_out + x * 4] = r
                rgba[row_out + x * 4 + 1] = g
                rgba[row_out + x * 4 + 2] = b
                rgba[row_out + x * 4 + 3] = a ^ alpha_flip
        return Image.frombytes("RGBA", (w, h), bytes(rgba))


def encode_crx(img: Image.Image, comp_level: int = 9) -> bytes:
    """Encode PIL Image to CRX format (Mode 0, Comp 2)."""
    has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
    w, h = img.size

    if not has_alpha:
        img = img.convert("RGB")
        pixel_size = 3
        stride = (w * pixel_size + 3) & ~3
        raw = bytearray(h * stride)
        rgb_data = img.tobytes()

        for y in range(h):
            row_in = y * w * 3
            row_out = y * stride
            for x in range(w):
                r = rgb_data[row_in + x * 3]
                g = rgb_data[row_in + x * 3 + 1]
                b = rgb_data[row_in + x * 3 + 2]
                raw[row_out + x * 3] = b
                raw[row_out + x * 3 + 1] = g
                raw[row_out + x * 3 + 2] = r
        depth = 0
    else:
        img = img.convert("RGBA")
        pixel_size = 4
        stride = (w * pixel_size + 3) & ~3
        raw = bytearray(h * stride)
        rgba_data = img.tobytes()

        for y in range(h):
            row_in = y * w * 4
            row_out = y * stride
            for x in range(w):
                r = rgba_data[row_in + x * 4]
                g = rgba_data[row_in + x * 4 + 1]
                b = rgba_data[row_in + x * 4 + 2]
                a = rgba_data[row_in + x * 4 + 3]
                raw[row_out + x * 4] = a ^ 0xFF
                raw[row_out + x * 4 + 1] = b
                raw[row_out + x * 4 + 2] = g
                raw[row_out + x * 4 + 3] = r
        depth = 1

    src_stride = w * pixel_size
    filtered = bytearray()

    for y in range(h):
        curr_row = y * stride
        prev_row = (y - 1) * stride

        # Candidate 0: Sub (left)
        cand0 = bytearray([0])
        cand0.extend(raw[curr_row:curr_row + pixel_size])
        for x in range(pixel_size, src_stride):
            cand0.append((raw[curr_row + x] - raw[curr_row + x - pixel_size]) & 0xFF)

        # Candidate 1: Up (above)
        if y > 0:
            cand1 = bytearray([1])
            for x in range(src_stride):
                cand1.append((raw[curr_row + x] - raw[prev_row + x]) & 0xFF)

            # Candidate 2: Up-Left
            cand2 = bytearray([2])
            cand2.extend(raw[curr_row:curr_row + pixel_size])
            for x in range(pixel_size, src_stride):
                cand2.append((raw[curr_row + x] - raw[prev_row + x - pixel_size]) & 0xFF)
        else:
            cand1 = cand0
            cand2 = cand0

        def score(buf):
            return sum(b if b < 128 else 256 - b for b in buf[1:])

        best = min([cand0, cand1, cand2], key=score)
        filtered.extend(best)

    payload = zlib.compress(bytes(filtered), level=comp_level)
    hdr = struct.pack("<4shhhhHHHH", SIGNATURE, 0, 0, w, h, 2, 1, depth, 0)
    return hdr + payload


def cmd_encode(input_path: str, output_path: str, resize: tuple[int, int] | None = None):
    img = Image.open(input_path)
    if resize is not None and img.size != resize:
        img = img.resize(resize, Image.Resampling.LANCZOS)
    crx_data = encode_crx(img)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(crx_data)
    print(f"Encoded {input_path} ({img.size[0]}x{img.size[1]}) -> {output_path} ({len(crx_data)} bytes)")


def cmd_decode(input_path: str, output_path: str):
    data = open(input_path, "rb").read()
    img = decode_crx(data)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    img.save(output_path)
    print(f"Decoded {input_path} -> {output_path} ({img.size[0]}x{img.size[1]})")


def cmd_batch_convert(in_dir: str, out_dir: str, resize: tuple[int, int] | None = None):
    os.makedirs(out_dir, exist_ok=True)
    files = [f for f in os.listdir(in_dir) if f.lower().endswith((".png", ".jpg", ".bmp"))]
    print(f"Converting {len(files)} images from {in_dir} to {out_dir}...")
    for idx, fname in enumerate(files):
        in_file = os.path.join(in_dir, fname)
        base_name = os.path.splitext(fname)[0]
        out_file = os.path.join(out_dir, base_name + ".CRX")
        img = Image.open(in_file)
        if resize is not None and img.size != resize:
            img = img.resize(resize, Image.Resampling.LANCZOS)
        crx_bytes = encode_crx(img)
        with open(out_file, "wb") as f:
            f.write(crx_bytes)
        if (idx + 1) % 50 == 0 or idx + 1 == len(files):
            print(f"  Processed {idx + 1}/{len(files)} images...")
    print("Batch conversion completed successfully.")


def main():
    parser = argparse.ArgumentParser(description="D.C.II P.C. CRX Encoder / Decoder")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_enc = sub.add_parser("encode", help="Encode image to CRX")
    p_enc.add_argument("input", help="Input image file")
    p_enc.add_argument("output", help="Output .CRX file")
    p_enc.add_argument("--resize", nargs=2, type=int, metavar=("W", "H"), help="Resize target")

    p_dec = sub.add_parser("decode", help="Decode CRX to image")
    p_dec.add_argument("input", help="Input .CRX file")
    p_dec.add_argument("output", help="Output image file")

    p_batch = sub.add_parser("batch_convert", help="Batch convert directory of images to CRX")
    p_batch.add_argument("indir", help="Input image directory")
    p_batch.add_argument("outdir", help="Output CRX directory")
    p_batch.add_argument("--resize", nargs=2, type=int, metavar=("W", "H"), help="Resize target")

    args = parser.parse_args()
    resize_tuple = tuple(args.resize) if args.resize else None

    if args.cmd == "encode":
        cmd_encode(args.input, args.output, resize_tuple)
    elif args.cmd == "decode":
        cmd_decode(args.input, args.output)
    elif args.cmd == "batch_convert":
        cmd_batch_convert(args.indir, args.outdir, resize_tuple)


if __name__ == "__main__":
    main()
