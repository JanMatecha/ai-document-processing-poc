#!/usr/bin/env python3
"""Run local MarkItDown and Docling conversions for configured documents."""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
DEFAULT_CONFIG = PROJECT_ROOT / "test_documents.yaml"
RESULTS_JSON = PROJECT_ROOT / "results" / "benchmark.json"
RESULTS_MARKDOWN = PROJECT_ROOT / "results" / "BENCHMARK.md"
TOOLS = ("markitdown", "docling")

sys.path.insert(0, str(SRC_DIR))

from benchmark_config import TestDocument, load_test_documents  # noqa: E402
from local_converters import (  # noqa: E402
    SUPPORTED_EXTENSIONS,
    UnsupportedFormatError,
    convert_document,
    converter_version,
    write_markdown,
)


HEADING_RE = re.compile(r"(?m)^#{1,6}\s+\S")
TABLE_SEPARATOR_RE = re.compile(
    r"(?m)^\s*\|(?:\s*:?-{3,}:?\s*\|){2,}\s*$"
)
IMAGE_MARKER_RE = re.compile(r"!\[[^\]]*\]\([^\n)]+\)|<!--\s*image\s*-->", re.I)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("hodnota musí být alespoň 1")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lokálně zpracuje veřejný testovací dataset oběma konvertory."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Cesta ke konfiguraci (výchozí: test_documents.yaml)",
    )
    parser.add_argument(
        "--document",
        action="append",
        dest="document_ids",
        metavar="ID",
        help="Zpracuje jen vybrané id; argument lze opakovat.",
    )
    parser.add_argument(
        "--tool",
        action="append",
        choices=TOOLS,
        dest="tools",
        help="Spustí jen vybraný nástroj; argument lze opakovat.",
    )
    parser.add_argument(
        "--repeat",
        type=positive_int,
        default=1,
        help="Počet opakování každé konverze (výchozí: 1).",
    )
    return parser.parse_args()


def select_documents(
    documents: list[TestDocument], requested_ids: list[str] | None
) -> list[TestDocument]:
    if not requested_ids:
        return documents
    by_id = {document.id: document for document in documents}
    unknown = sorted(set(requested_ids) - set(by_id))
    if unknown:
        raise ValueError(f"Neznámé id dokumentu: {', '.join(unknown)}")
    requested = set(requested_ids)
    return [document for document in documents if document.id in requested]


def markdown_indicators(markdown: str) -> dict[str, int]:
    return {
        "headings": len(HEADING_RE.findall(markdown)),
        "tables": len(TABLE_SEPARATOR_RE.findall(markdown)),
        "image_markers": len(IMAGE_MARKER_RE.findall(markdown)),
    }


def relative_posix(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def base_record(
    document: TestDocument,
    tool: str,
    repeat: int,
    timestamp: str,
    source: Path,
) -> dict[str, Any]:
    return {
        "run_timestamp_utc": timestamp,
        "document_id": document.id,
        "document_name": document.name,
        "content_group": document.content_group,
        "filename": document.local_filename,
        "format": document.format,
        "category": document.category,
        "converter": tool,
        "converter_version": converter_version(tool),
        "repeat": repeat,
        "elapsed_seconds": None,
        "input_size_bytes": source.stat().st_size if source.is_file() else None,
        "markdown_characters": 0,
        "headings": 0,
        "tables": 0,
        "image_markers": 0,
        "status": "pending",
        "error": None,
        "output_path": None,
    }


def run_conversion(
    document: TestDocument,
    tool: str,
    repeat: int,
    timestamp: str,
) -> dict[str, Any]:
    source = document.local_path(PROJECT_ROOT)
    record = base_record(document, tool, repeat, timestamp, source)

    if not source.is_file():
        record["status"] = "missing"
        record["error"] = (
            "Vstupní soubor chybí; spusťte python scripts/download_test_documents.py"
        )
        return record

    if source.suffix.lower() not in SUPPORTED_EXTENSIONS[tool]:
        record["status"] = "unsupported"
        record["error"] = f"{tool} nepodporuje formát {document.format}"
        return record

    started = perf_counter()
    try:
        markdown = convert_document(tool, source)
        elapsed = perf_counter() - started
        destination = PROJECT_ROOT / "output" / "public" / document.id / f"{tool}.md"
        write_markdown(markdown, destination)
    except UnsupportedFormatError as exc:
        record["elapsed_seconds"] = round(perf_counter() - started, 6)
        record["status"] = "unsupported"
        record["error"] = str(exc)
        return record
    except Exception as exc:
        record["elapsed_seconds"] = round(perf_counter() - started, 6)
        record["status"] = "failed"
        record["error"] = f"{type(exc).__name__}: {exc}"
        return record

    indicators = markdown_indicators(markdown)
    record.update(
        {
            "elapsed_seconds": round(elapsed, 6),
            "markdown_characters": len(markdown),
            "headings": indicators["headings"],
            "tables": indicators["tables"],
            "image_markers": indicators["image_markers"],
            "status": "success",
            "output_path": relative_posix(destination),
        }
    )
    return record


def load_existing_records(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    records = payload.get("records") if isinstance(payload, dict) else None
    return records if isinstance(records, list) else []


def merge_records(
    existing: list[dict[str, Any]], current: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    replaced_pairs = {
        (record["document_id"], record["converter"]) for record in current
    }
    preserved = [
        record
        for record in existing
        if (record.get("document_id"), record.get("converter")) not in replaced_pairs
    ]
    return preserved + current


def write_json(
    records: list[dict[str, Any]], timestamp: str, config_path: Path
) -> None:
    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "generated_at_utc": timestamp,
        "config": (
            relative_posix(config_path)
            if config_path.is_relative_to(PROJECT_ROOT)
            else str(config_path)
        ),
        "records": records,
    }
    temporary = RESULTS_JSON.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(RESULTS_JSON)


def escape_cell(value: object) -> str:
    if value is None:
        return "-"
    return str(value).replace("|", "\\|").replace("\n", " ")


def format_seconds(value: object) -> str:
    return f"{value:.3f}" if isinstance(value, (int, float)) else "-"


def record_sort_key(
    record: dict[str, Any], document_order: dict[str, int]
) -> tuple[int, int, int]:
    tool_order = {"markitdown": 0, "docling": 1}
    return (
        document_order.get(str(record.get("document_id")), len(document_order)),
        tool_order.get(str(record.get("converter")), len(tool_order)),
        int(record.get("repeat", 0)),
    )


def aggregate_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for record in records:
        key = (str(record.get("document_id")), str(record.get("converter")))
        grouped.setdefault(key, []).append(record)

    aggregate: list[dict[str, Any]] = []
    for group in grouped.values():
        successes = [record for record in group if record.get("status") == "success"]
        representative = successes[-1] if successes else group[-1]
        times = [
            float(record["elapsed_seconds"])
            for record in successes
            if isinstance(record.get("elapsed_seconds"), (int, float))
        ]
        row = dict(representative)
        row["mean_elapsed_seconds"] = statistics.fmean(times) if times else None
        row["status"] = (
            "success"
            if len(successes) == len(group)
            else ", ".join(sorted({str(record.get("status")) for record in group}))
        )
        aggregate.append(row)
    return aggregate


def write_markdown_report(
    records: list[dict[str, Any]], documents: list[TestDocument], timestamp: str
) -> None:
    document_order = {document.id: index for index, document in enumerate(documents)}
    sorted_records = sorted(records, key=lambda row: record_sort_key(row, document_order))
    lines = [
        "# Public document benchmark",
        "",
        f"Generated: `{timestamp}`",
        "",
        "This report contains objective conversion metadata only. Semantic quality still requires manual review of each Markdown output against its source document.",
        "",
        "## Overview",
        "",
        "| Document | Format | Tool | Repeat | Time (s) | Output chars | Headings | Tables | Image markers | Status |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for record in sorted_records:
        lines.append(
            "| {document} | {format} | {tool} | {repeat} | {time} | {chars} | "
            "{headings} | {tables} | {images} | {status} |".format(
                document=escape_cell(record.get("document_name")),
                format=escape_cell(str(record.get("format", "")).upper()),
                tool=escape_cell(record.get("converter")),
                repeat=escape_cell(record.get("repeat")),
                time=format_seconds(record.get("elapsed_seconds")),
                chars=escape_cell(record.get("markdown_characters")),
                headings=escape_cell(record.get("headings")),
                tables=escape_cell(record.get("tables")),
                images=escape_cell(record.get("image_markers")),
                status=escape_cell(record.get("status")),
            )
        )

    lines.extend(
        [
            "",
            "## Cross-format comparison",
            "",
            "Mean time is calculated across successful repeats. Links point to the latest successful local Markdown output.",
        ]
    )
    by_group: dict[str, list[TestDocument]] = {}
    for document in documents:
        by_group.setdefault(document.content_group, []).append(document)
    aggregate = aggregate_records(records)
    aggregate_by_pair = {
        (str(record.get("document_id")), str(record.get("converter"))): record
        for record in aggregate
    }

    for content_group, group_documents in by_group.items():
        if len(group_documents) < 2:
            continue
        group_rows: list[dict[str, Any]] = []
        for document in group_documents:
            for tool in TOOLS:
                existing = aggregate_by_pair.get((document.id, tool))
                group_rows.append(
                    existing
                    if existing is not None
                    else {
                        "document_id": document.id,
                        "format": document.format,
                        "converter": tool,
                        "status": "not run",
                    }
                )
        lines.extend(
            [
                "",
                f"### {group_documents[0].name.rsplit(' (', 1)[0]}",
                "",
                "| Source format | Tool | Mean time (s) | Output chars | Headings | Tables | Image markers | Status | Output |",
                "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
            ]
        )
        for record in sorted(
            group_rows, key=lambda row: record_sort_key(row, document_order)
        ):
            output_path = record.get("output_path")
            output_link = (
                f"[Markdown](../{output_path})" if isinstance(output_path, str) else "-"
            )
            lines.append(
                "| {format} | {tool} | {time} | {chars} | {headings} | {tables} | "
                "{images} | {status} | {output} |".format(
                    format=escape_cell(str(record.get("format", "")).upper()),
                    tool=escape_cell(record.get("converter")),
                    time=format_seconds(record.get("mean_elapsed_seconds")),
                    chars=escape_cell(record.get("markdown_characters")),
                    headings=escape_cell(record.get("headings")),
                    tables=escape_cell(record.get("tables")),
                    images=escape_cell(record.get("image_markers")),
                    status=escape_cell(record.get("status")),
                    output=output_link,
                )
            )

    problems = [record for record in sorted_records if record.get("status") != "success"]
    recorded_pairs = {
        (str(record.get("document_id")), str(record.get("converter")))
        for record in records
    }
    missing_pairs = [
        (document.id, tool)
        for document in documents
        for tool in TOOLS
        if (document.id, tool) not in recorded_pairs
    ]
    lines.extend(["", "## Limitations and failures", ""])
    if not problems and not missing_pairs:
        lines.append("No conversion failures or unsupported formats were recorded.")
    elif not problems:
        lines.append("No conversion failures or unsupported formats were recorded in completed runs.")
    else:
        for record in problems:
            lines.append(
                f"- `{record.get('document_id')}` / `{record.get('converter')}` / "
                f"`{record.get('status')}`: {escape_cell(record.get('error'))}"
            )
    if missing_pairs:
        lines.extend(
            [
                "",
                "The following configured combinations have no result record yet (not run):",
                "",
            ]
        )
        for document_id, tool in missing_pairs:
            lines.append(f"- `{document_id}` / `{tool}`")

    RESULTS_MARKDOWN.parent.mkdir(parents=True, exist_ok=True)
    temporary = RESULTS_MARKDOWN.with_suffix(".md.tmp")
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(RESULTS_MARKDOWN)


def main() -> int:
    args = parse_args()
    try:
        documents = load_test_documents(args.config.resolve())
        selected_documents = select_documents(documents, args.document_ids)
    except ValueError as exc:
        print(f"Chyba konfigurace: {exc}", file=sys.stderr)
        return 2

    selected_tools = list(dict.fromkeys(args.tools or TOOLS))
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    current_records: list[dict[str, Any]] = []

    for document in selected_documents:
        print(f"\n{document.id} ({document.format.upper()})", flush=True)
        for tool in selected_tools:
            for repeat in range(1, args.repeat + 1):
                print(f"  {tool:<10} repeat {repeat}: running", flush=True)
                record = run_conversion(document, tool, repeat, timestamp)
                current_records.append(record)
                print(
                    f"  {tool:<10} repeat {repeat}: {record['status']:<11} "
                    f"{format_seconds(record['elapsed_seconds'])} s, "
                    f"{record['markdown_characters']:,} znaků"
                )
                if record.get("error"):
                    print(f"    {record['error']}")

    existing_records = load_existing_records(RESULTS_JSON)
    merged_records = merge_records(existing_records, current_records)
    document_order = {document.id: index for index, document in enumerate(documents)}
    merged_records.sort(key=lambda row: record_sort_key(row, document_order))
    write_json(merged_records, timestamp, args.config.resolve())
    write_markdown_report(merged_records, documents, timestamp)

    successes = sum(record["status"] == "success" for record in current_records)
    print("\nSouhrn benchmarku")
    print(f"  Konverzí: {len(current_records)}")
    print(f"  Úspěšných: {successes}")
    print(f"  JSON: {RESULTS_JSON}")
    print(f"  Report: {RESULTS_MARKDOWN}")

    failed = any(
        record["status"] in {"failed", "missing"} for record in current_records
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
