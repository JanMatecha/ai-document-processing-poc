"""Shared local-only conversion helpers for MarkItDown and Docling."""

from __future__ import annotations

import os
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Callable


TOOLS = ("markitdown", "docling")
SUPPORTED_EXTENSIONS = {
    "markitdown": frozenset({".pdf", ".docx", ".pptx", ".xlsx"}),
    "docling": frozenset({".pdf", ".docx", ".pptx", ".xlsx"}),
}


class UnsupportedFormatError(ValueError):
    """Raised when a configured tool does not support an input extension."""


def resolve_input(input_path: Path) -> Path:
    """Return an absolute existing file path without modifying the source."""
    try:
        resolved = input_path.expanduser().resolve(strict=True)
    except FileNotFoundError as exc:
        raise ValueError(f"Vstupní soubor neexistuje: {input_path}") from exc

    if not resolved.is_file():
        raise ValueError(f"Vstupní cesta není soubor: {resolved}")
    return resolved


def converter_version(tool: str) -> str:
    """Return the installed converter version or a stable fallback label."""
    normalized = normalize_tool(tool)
    try:
        return version(normalized)
    except PackageNotFoundError:
        return "neznámá"


def normalize_tool(tool: str) -> str:
    normalized = tool.strip().lower()
    if normalized not in TOOLS:
        raise ValueError(f"Neznámý konvertor: {tool}")
    return normalized


def ensure_supported(tool: str, source: Path) -> None:
    normalized = normalize_tool(tool)
    suffix = source.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS[normalized]:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS[normalized]))
        raise UnsupportedFormatError(
            f"{normalized} nepodporuje příponu {suffix or '<bez přípony>'}; "
            f"podporováno: {supported}"
        )


def write_markdown(markdown: str, destination: Path) -> None:
    """Atomically write UTF-8 Markdown while preserving older output on failure."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(markdown, encoding="utf-8", newline="\n")
    temporary.replace(destination)


def _convert_markitdown(source: Path) -> str:
    from markitdown import MarkItDown

    # Plugins, LLM clients and cloud endpoints are deliberately not enabled.
    converter = MarkItDown(enable_plugins=False)
    result = converter.convert_local(source)
    markdown = result.text_content
    if not isinstance(markdown, str):
        raise TypeError("MarkItDown nevrátil textový Markdown.")
    return markdown


def _convert_docling(source: Path) -> str:
    # Docling 2.118 enables torch.compile by default. Eager inference avoids an
    # optional MSVC C++ toolchain on a standard Windows workstation.
    os.environ["DOCLING_INFERENCE_COMPILE_TORCH_MODELS"] = "false"

    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    # Remote services and third-party plugins remain disabled explicitly for
    # the PDF pipeline. Office formats use Docling's local declarative backends.
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
    if not isinstance(markdown, str):
        raise TypeError("Docling nevrátil textový Markdown.")
    return markdown


CONVERTERS: dict[str, Callable[[Path], str]] = {
    "markitdown": _convert_markitdown,
    "docling": _convert_docling,
}


def convert_document(tool: str, input_path: Path) -> str:
    """Convert one supported local file without using remote processing."""
    normalized = normalize_tool(tool)
    source = resolve_input(input_path)
    ensure_supported(normalized, source)
    return CONVERTERS[normalized](source)
