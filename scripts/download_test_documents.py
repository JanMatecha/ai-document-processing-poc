#!/usr/bin/env python3
"""Download configured public benchmark documents into input/public/."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
DEFAULT_CONFIG = PROJECT_ROOT / "test_documents.yaml"
USER_AGENT = "document-ingestion-poc/2.0 (+https://github.com/JanMatecha/ai-document-processing-poc)"
CHUNK_SIZE = 1024 * 1024

sys.path.insert(0, str(SRC_DIR))

from benchmark_config import TestDocument, load_test_documents  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stáhne chybějící veřejné dokumenty definované v YAML konfiguraci."
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
        help="Stáhne jen vybrané id; argument lze opakovat.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Znovu stáhne i již existující soubory.",
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


def validate_download(path: Path, document_format: str) -> None:
    size = path.stat().st_size
    if size == 0:
        raise ValueError("server vrátil prázdný soubor")

    with path.open("rb") as stream:
        signature = stream.read(8)
    if document_format == "pdf" and not signature.startswith(b"%PDF-"):
        raise ValueError("stažený obsah není PDF")
    if document_format in {"docx", "pptx", "xlsx"} and not signature.startswith(b"PK"):
        raise ValueError(f"stažený obsah není platný {document_format.upper()} ZIP kontejner")


def download_document(document: TestDocument, destination: Path) -> int:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    temporary.unlink(missing_ok=True)

    request = Request(
        document.source_url,
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
    )
    try:
        with urlopen(request, timeout=120) as response, temporary.open("wb") as output:
            shutil.copyfileobj(response, output, length=CHUNK_SIZE)
        validate_download(temporary, document.format)
        size = temporary.stat().st_size
        temporary.replace(destination)
        return size
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def main() -> int:
    args = parse_args()
    try:
        documents = load_test_documents(args.config.resolve())
        selected = select_documents(documents, args.document_ids)
    except ValueError as exc:
        print(f"Chyba konfigurace: {exc}", file=sys.stderr)
        return 2

    downloaded = 0
    skipped = 0
    failures: list[tuple[str, str]] = []

    for document in selected:
        destination = document.local_path(PROJECT_ROOT)
        if destination.exists() and not args.force:
            print(
                f"SKIP     {document.id}: {destination.name} "
                f"({destination.stat().st_size:,} B)"
            )
            skipped += 1
            continue

        print(f"DOWNLOAD {document.id}: {document.source_url}")
        try:
            size = download_document(document, destination)
        except (HTTPError, URLError, OSError, ValueError) as exc:
            message = f"{type(exc).__name__}: {exc}"
            print(f"FAILED   {document.id}: {message}", file=sys.stderr)
            failures.append((document.id, message))
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            print(f"FAILED   {document.id}: {message}", file=sys.stderr)
            failures.append((document.id, message))
        else:
            print(f"OK       {document.id}: {destination} ({size:,} B)")
            downloaded += 1

    print("\nSouhrn stahování")
    print(f"  Vybráno:   {len(selected)}")
    print(f"  Staženo:   {downloaded}")
    print(f"  Přeskočeno:{skipped:>4}")
    print(f"  Selhalo:   {len(failures)}")
    if failures:
        for document_id, message in failures:
            print(f"  - {document_id}: {message}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
