#!/usr/bin/env python3
"""Optimize church photos for the static site.

- Strips ALL metadata (EXIF/GPS) for privacy.
- Corrects the upside-down source photo.
- Emits sized WebP + JPEG fallbacks into site/assets/img.
"""
import os
from PIL import Image, ImageOps

RAW = os.path.join(os.path.dirname(__file__), "assets-raw")
OUT = os.path.join(os.path.dirname(__file__), "site", "assets", "img")
os.makedirs(OUT, exist_ok=True)

# source hash -> (friendly name, rotate_degrees, alt text)
MAP = {
    "394b18_93042e8f88a34e0faec4dc60d2d1a2a3": (
        "hero-fellowship", 0,
        "Members of Christian Church In Raleigh gathered together in fellowship"),
    "394b18_4a10caa926bc4f52a5fc323cb34eb56f": (
        "gallery-bible-study", 0,
        "A small group seated together for Bible study with Scripture in hand"),
    "394b18_5f374636fba04494ba4fcb97f6640a39": (
        "gallery-group-smiles", 0,
        "A group of believers smiling together after a gathering"),
    "394b18_762bd6c15cd7446283c8453213ec8787": (
        "gallery-smores", 0,
        "Two members enjoying s'mores under string lights at a fellowship evening"),
    "394b18_4932de3f908f4f7f8fae5979bdb9abc1": (
        "gallery-outdoor-singing", 0,
        "Outdoor gathering with a guitar and singing together"),
    "394b18_93bd78eae4a24cc2961e86925dfafa66": (
        "gallery-group-dog", 0,
        "A joyful group photo during a home gathering"),
    "394b18_9f54feb61fb94ec887e254d56f8e291c": (
        "gallery-together", 0,
        "Believers gathered together in fellowship"),
    "394b18_d0a7fa7dc1284c3fa35100bc286cb402": (
        "gallery-cafe", 0,
        "A relaxed gathering of the church family"),
    "394b18_e285b1a2868a47089713b3c5cb668a0f": (
        "gallery-home-group", 0,
        "A home gathering meeting together around the Word"),
    "394b18_eb257eae68cb4f27a6602e83016bf23c": (
        "gallery-table", 0,
        "Members sharing a meal and fellowship around the table"),
    "394b18_fd7219ff54b64655b27d0e089a2dd2ee": (
        "gallery-meal", 0,
        "Sharing a meal together as a church family"),
    "394b18_b114dceb59eb4d9d9d4d7d4221421703": (
        "texture-porch", 0,
        "The doorway of a home where the church gathers"),
}

# widths to emit per role
HERO = [1920, 1280, 800]
GALLERY = [1000, 600]


def load(path):
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)  # honor camera orientation first
    return im.convert("RGB")


def save_variants(im, name, widths, is_hero=False):
    results = []
    w0, h0 = im.size
    for w in widths:
        if w > w0:
            w = w0
        h = round(h0 * (w / w0))
        rs = im.resize((w, h), Image.LANCZOS)
        # WebP (metadata stripped: PIL writes none by default here)
        wp = os.path.join(OUT, f"{name}-{w}.webp")
        rs.save(wp, "WEBP", quality=80, method=6)
        # JPEG fallback (no exif passed => stripped)
        jp = os.path.join(OUT, f"{name}-{w}.jpg")
        rs.save(jp, "JPEG", quality=82, optimize=True, progressive=True)
        results.append((w, os.path.getsize(wp), os.path.getsize(jp)))
    return results


def main():
    for h, (name, rot, _alt) in MAP.items():
        src = None
        for ext in (".jpg", ".jpeg", ".png"):
            p = os.path.join(RAW, h + ext)
            if os.path.exists(p):
                src = p
                break
        if not src:
            print("MISSING", h)
            continue
        im = load(src)
        if rot:
            im = im.rotate(rot, expand=True)
        is_hero = name.startswith("hero")
        widths = HERO if is_hero else GALLERY
        r = save_variants(im, name, widths, is_hero)
        print(f"{name:24s} {im.size[0]}x{im.size[1]} -> {[w for w,_,_ in r]}")


if __name__ == "__main__":
    main()
