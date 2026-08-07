#!/usr/bin/env python3
"""Convert one local document to Markdown with Docling."""

from __future__ import annotations

import argparse
import os
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from time import perf_counter


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "output" / "docling"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lokální převod jednoho dokumentu do Markdownu pomocí Doclingu."
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

        # Docling 2.118 enables torch.compile by default. On a standard Windows
        # workstation that can require the optional MSVC C++ compiler (cl.exe).
        # Eager inference keeps this PoC self-contained and produces the same
        # document model without requiring a native build toolchain.
        os.environ["DOCLING_INFERENCE_COMPILE_TORCH_MODELS"] = "false"

        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.document_converter import DocumentConverter, PdfFormatOption

        started = perf_counter()

        # Remote services and third-party plugins remain disabled explicitly.
        # Docling may download model weights on the first PDF run, but it never
        # sends the input document to those model repositories.
        pdf_options = PdfPipelineOptions(
            enable_remote_services=False,
            allow_external_plugins=False,
        )
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_options)
            }
        )

        result = converter.convert(source)
        markdown = result.document.export_to_markdown()
        elapsed = perf_counter() - started

        if not isinstance(markdown, str):
            raise TypeError("Docling nevrátil textový Markdown.")

        destination = OUTPUT_DIR / f"{source.stem}.md"
        write_markdown(markdown, destination)
    except (ImportError, OSError, RuntimeError, TypeError, ValueError) as exc:
        print(f"Chyba Docling: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # Preserve a concise CLI for conversion-specific errors.
        print(
            f"Neočekávaná chyba Docling ({type(exc).__name__}): {exc}",
            file=sys.stderr,
        )
        return 1

    print("Zpracování dokončeno")
    print(f"  Nástroj:       Docling {package_version('docling')}")
    print(f"  Vstup:         {source}")
    print(f"  Velikost:      {source.stat().st_size:,} B")
    print(f"  Výstup:        {destination}")
    print(f"  Markdown:      {len(markdown):,} znaků")
    print(f"  Doba převodu:  {elapsed:.3f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
