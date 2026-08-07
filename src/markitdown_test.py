#!/usr/bin/env python3
"""Convert one local document to Markdown with Microsoft MarkItDown."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from time import perf_counter

from local_converters import (
    convert_document,
    converter_version,
    resolve_input,
    write_markdown,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "output" / "markitdown"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lokální převod jednoho dokumentu do Markdownu pomocí MarkItDown."
    )
    parser.add_argument("input", type=Path, help="Cesta ke vstupnímu dokumentu")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        source = resolve_input(args.input)
        started = perf_counter()
        markdown = convert_document("markitdown", source)
        elapsed = perf_counter() - started
        destination = OUTPUT_DIR / f"{source.stem}.md"
        write_markdown(markdown, destination)
    except (ImportError, OSError, RuntimeError, TypeError, ValueError) as exc:
        print(f"Chyba MarkItDown: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # The library exposes format-specific exception types.
        print(
            f"Neočekávaná chyba MarkItDown ({type(exc).__name__}): {exc}",
            file=sys.stderr,
        )
        return 1

    print("Zpracování dokončeno")
    print(f"  Nástroj:       MarkItDown {converter_version('markitdown')}")
    print(f"  Vstup:         {source}")
    print(f"  Velikost:      {source.stat().st_size:,} B")
    print(f"  Výstup:        {destination}")
    print(f"  Markdown:      {len(markdown):,} znaků")
    print(f"  Doba převodu:  {elapsed:.3f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
