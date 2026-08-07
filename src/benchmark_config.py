"""Validation and loading of the public benchmark document definition."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import yaml


SUPPORTED_FORMATS = frozenset({"pdf", "docx", "pptx", "xlsx"})
REQUIRED_FIELDS = (
    "id",
    "name",
    "source_url",
    "local_filename",
    "format",
    "category",
    "description",
    "expected_features",
)


@dataclass(frozen=True)
class TestDocument:
    id: str
    content_group: str
    name: str
    source_page: str | None
    source_url: str
    local_filename: str
    format: str
    category: str
    description: str
    expected_features: tuple[str, ...]

    def local_path(self, project_root: Path) -> Path:
        return project_root / "input" / "public" / self.local_filename


def _required_string(item: dict, field: str, index: int) -> str:
    value = item.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Dokument #{index}: pole '{field}' musí být neprázdný text.")
    return value.strip()


def _valid_https_url(value: str, field: str, document_id: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(
            f"Dokument '{document_id}': pole '{field}' musí být platná HTTPS URL."
        )
    return value


def load_test_documents(config_path: Path) -> list[TestDocument]:
    """Load and validate a YAML document list."""
    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Konfigurace neexistuje: {config_path}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"Neplatný YAML v {config_path}: {exc}") from exc

    if not isinstance(payload, dict) or not isinstance(payload.get("documents"), list):
        raise ValueError("Konfigurace musí obsahovat seznam 'documents'.")

    documents: list[TestDocument] = []
    seen_ids: set[str] = set()
    seen_filenames: set[str] = set()

    for index, item in enumerate(payload["documents"], start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Dokument #{index} musí být YAML objekt.")
        missing = [field for field in REQUIRED_FIELDS if field not in item]
        if missing:
            raise ValueError(f"Dokument #{index}: chybí pole {', '.join(missing)}.")

        document_id = _required_string(item, "id", index)
        if document_id in seen_ids:
            raise ValueError(f"Duplicitní id dokumentu: {document_id}")
        if not document_id.replace("_", "").isalnum() or document_id.lower() != document_id:
            raise ValueError(
                f"Dokument '{document_id}': id smí obsahovat jen malá písmena, čísla a _."
            )

        local_filename = _required_string(item, "local_filename", index)
        if Path(local_filename).name != local_filename:
            raise ValueError(
                f"Dokument '{document_id}': local_filename nesmí obsahovat adresář."
            )
        if local_filename.lower() in seen_filenames:
            raise ValueError(f"Duplicitní local_filename: {local_filename}")

        document_format = _required_string(item, "format", index).lower()
        if document_format not in SUPPORTED_FORMATS:
            raise ValueError(
                f"Dokument '{document_id}': nepodporovaný formát {document_format}."
            )
        if Path(local_filename).suffix.lower() != f".{document_format}":
            raise ValueError(
                f"Dokument '{document_id}': formát neodpovídá příponě souboru."
            )

        features = item.get("expected_features")
        if not isinstance(features, list) or not features or not all(
            isinstance(value, str) and value.strip() for value in features
        ):
            raise ValueError(
                f"Dokument '{document_id}': expected_features musí být neprázdný seznam textů."
            )

        source_url = _valid_https_url(
            _required_string(item, "source_url", index), "source_url", document_id
        )
        source_page_value = item.get("source_page")
        source_page = None
        if source_page_value is not None:
            if not isinstance(source_page_value, str) or not source_page_value.strip():
                raise ValueError(
                    f"Dokument '{document_id}': source_page musí být neprázdný text."
                )
            source_page = _valid_https_url(
                source_page_value.strip(), "source_page", document_id
            )

        content_group_value = item.get("content_group", document_id)
        if not isinstance(content_group_value, str) or not content_group_value.strip():
            raise ValueError(
                f"Dokument '{document_id}': content_group musí být neprázdný text."
            )

        documents.append(
            TestDocument(
                id=document_id,
                content_group=content_group_value.strip(),
                name=_required_string(item, "name", index),
                source_page=source_page,
                source_url=source_url,
                local_filename=local_filename,
                format=document_format,
                category=_required_string(item, "category", index),
                description=_required_string(item, "description", index),
                expected_features=tuple(value.strip() for value in features),
            )
        )
        seen_ids.add(document_id)
        seen_filenames.add(local_filename.lower())

    if not documents:
        raise ValueError("Konfigurace neobsahuje žádné dokumenty.")
    return documents
