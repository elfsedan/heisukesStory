#!/usr/bin/env python3
"""
manga_webp_ao3.py

Konvertiert alle PNG/JPG-Bilder in einem Ordner nach WebP und erzeugt
fertige AO3-<img>-Tags mit den passenden GitHub-Pages-URLs.

Benötigt: Pillow  ->  pip install Pillow

Beispielaufruf:
    python manga_webp_ao3.py ./ep01 \
        --base-url https://DEINUSERNAME.github.io/manga-hosting/reincarnation-of-hope/ep01 \
        --quality 85 --width 1000 --max-width 1600
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Fehler: Pillow ist nicht installiert. Bitte 'pip install Pillow' ausführen.")

# Eingabeformate, die verarbeitet werden
SOURCE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


def sanitize(name: str) -> str:
    """Macht Dateinamen URL-sicher: nur a-z, 0-9, -, _."""
    safe = []
    for ch in name.lower():
        if ch.isalnum() and ch.isascii():
            safe.append(ch)
        elif ch in ("-", "_"):
            safe.append(ch)
        else:
            safe.append("-")  # alles andere -> Bindestrich
    # Mehrfach-Bindestriche zusammenfassen
    result = "".join(safe)
    while "--" in result:
        result = result.replace("--", "-")
    return result.strip("-")


def convert_folder(src_dir: Path, quality: int, lossless: bool, max_width: int):
    """Konvertiert alle passenden Bilder nach WebP. Gibt Liste der Zieldateinamen zurück."""
    out_dir = src_dir / "webp"
    out_dir.mkdir(exist_ok=True)

    # Sortiert einsammeln, damit die Reihenfolge stimmt (page01, page02, ...)
    files = sorted(
        [p for p in src_dir.iterdir() if p.suffix.lower() in SOURCE_SUFFIXES],
        key=lambda p: p.name.lower(),
    )

    if not files:
        sys.exit(f"Keine passenden Bilddateien in {src_dir} gefunden.")

    produced = []
    for f in files:
        target_name = sanitize(f.stem) + ".webp"
        target = out_dir / target_name

        img = Image.open(f)
        # Alpha erhalten, falls vorhanden; sonst nach RGB
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

        # Herunterskalieren, wenn breiter als max_width (0 = kein Limit)
        note = ""
        if max_width and img.width > max_width:
            new_height = round(img.height * max_width / img.width)
            img = img.resize((max_width, new_height), Image.LANCZOS)
            note = f"  (skaliert auf {max_width}px)"

        save_kwargs = {"format": "WEBP", "method": 6}
        if lossless:
            save_kwargs["lossless"] = True
        else:
            save_kwargs["quality"] = quality

        img.save(target, **save_kwargs)
        produced.append(target_name)
        print(f"  {f.name}  ->  webp/{target_name}{note}")

    return produced


def build_tags(filenames, base_url: str, width: int):
    """Erzeugt AO3-img-Tags, getrennt durch einen Zeilenumbruch (<br />)."""
    base = base_url.rstrip("/")
    lines = []
    for i, name in enumerate(filenames, start=1):
        url = f"{base}/{name}"
        alt = f"Seite {i:02d}"
        width_attr = f' width="{width}"' if width else ""
        lines.append(f'<img src="{url}" alt="{alt}"{width_attr}><br />')
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(
        description="PNG/JPG -> WebP konvertieren und AO3-img-Tags erzeugen."
    )
    ap.add_argument("folder", help="Ordner mit den Quellbildern")
    ap.add_argument(
        "--base-url",
        default="https://DEINUSERNAME.github.io/manga-hosting/EPISODE",
        help="Basis-URL, unter der die WebP-Dateien später erreichbar sind",
    )
    ap.add_argument("--quality", type=int, default=85, help="WebP-Qualität 0-100 (Standard 85)")
    ap.add_argument("--lossless", action="store_true", help="Verlustfrei speichern (für Line-Art ideal, größer)")
    ap.add_argument("--width", type=int, default=1000, help="width-Attribut im HTML-Tag in px (0 = weglassen)")
    ap.add_argument("--max-width", type=int, default=1600, help="Bilder auf diese Pixelbreite herunterskalieren (0 = Originalgröße behalten)")
    args = ap.parse_args()

    src_dir = Path(args.folder).expanduser().resolve()
    if not src_dir.is_dir():
        sys.exit(f"Ordner nicht gefunden: {src_dir}")

    print(f"Konvertiere Bilder in: {src_dir}")
    produced = convert_folder(src_dir, args.quality, args.lossless, args.max_width)

    tags = build_tags(produced, args.base_url, args.width)
    tags_file = src_dir / "ao3_tags.txt"
    tags_file.write_text(tags + "\n", encoding="utf-8")

    print(f"\nFertig: {len(produced)} Dateien konvertiert.")
    print(f"WebP-Dateien liegen in: {src_dir / 'webp'}")
    print(f"AO3-Tags gespeichert in: {tags_file}")
    print("\n--- AO3-Tags (zum Kopieren) ---\n")
    print(tags)


if __name__ == "__main__":
    main()
