#!/usr/bin/env python3
"""Convert one local document to Markdown with Microsoft MarkItDown."""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from time import perf_counter


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "output" / "markitdown"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lokální převod jednoho dokumentu do Markdownu pomocí MarkItDown."
    )
    parser.add_argument("input", type=Path, help="Cesta ke vstupnímu dokumentu")
    return parser.parse_args()


def resolve_input(input_path: Path) -> Path:
    try:
        resolved = input_path.expanduser().resolve(strict=True)
    except FileNotFoundError as exc:
        raise ValueError(f"Vstupní soubor neexistuje: {input_path}") from exc

    if not resolved.is_file():
        raise ValueError(f"Vstupní cesta není soubor: {resolved}")
    return resolved


def package_version(distribution: str) -> str:
    try:
        return version(distribution)
    except PackageNotFoundError:
        return "neznámá"


def write_markdown(markdown: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(markdown, encoding="utf-8", newline="\n")
    temporary.replace(destination)


def main() -> int:
    args = parse_args()

    try:
        source = resolve_input(args.input)
        from markitdown import MarkItDown

        started = perf_counter()
        # Plugins, LLM clients and cloud endpoints are deliberately not enabled.
        converter = MarkItDown(enable_plugins=False)
        result = converter.convert_local(source)
        markdown = result.text_content
        elapsed = perf_counter() - started

        if not isinstance(markdown, str):
            raise TypeError("MarkItDown nevrátil textový Markdown.")

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
    print(f"  Nástroj:       MarkItDown {package_version('markitdown')}")
    print(f"  Vstup:         {source}")
    print(f"  Velikost:      {source.stat().st_size:,} B")
    print(f"  Výstup:        {destination}")
    print(f"  Markdown:      {len(markdown):,} znaků")
    print(f"  Doba převodu:  {elapsed:.3f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
