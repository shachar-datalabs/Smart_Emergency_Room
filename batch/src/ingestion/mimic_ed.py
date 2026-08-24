"""Local-first ingestion of MIMIC-IV-ED CSV archives into GCS and BigQuery."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import logging
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

LOGGER = logging.getLogger("smart_er.ingestion")
TABLES = ("edstays", "triage", "vitalsign")
HEADERS = {
    "edstays": (
        "subject_id",
        "hadm_id",
        "stay_id",
        "intime",
        "outtime",
        "gender",
        "race",
        "arrival_transport",
        "disposition",
    ),
    "triage": (
        "subject_id",
        "stay_id",
        "temperature",
        "heartrate",
        "resprate",
        "o2sat",
        "sbp",
        "dbp",
        "pain",
        "acuity",
        "chiefcomplaint",
    ),
    "vitalsign": (
        "subject_id",
        "stay_id",
        "charttime",
        "temperature",
        "heartrate",
        "resprate",
        "o2sat",
        "sbp",
        "dbp",
        "rhythm",
        "pain",
    ),
}


@dataclass(frozen=True)
class IngestionConfig:
    project: str
    bucket: str
    dataset: str
    location: str
    version: str
    source_dir: Path
    schema_dir: Path
    apply: bool = False
    replace: bool = False

    def object_uri(self, table: str) -> str:
        return f"gs://{self.bucket}/mimic-iv-ed/{self.version}/ed/{table}.csv.gz"


@dataclass(frozen=True)
class SourceValidation:
    table: str
    path: str
    size_bytes: int
    sha256: str
    row_count: int


Runner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


def default_runner(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    LOGGER.info("Running: %s", " ".join(command))
    return subprocess.run(command, check=True, capture_output=True, text=True)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _validate_file(table: str, path: Path) -> SourceValidation:
    if not path.is_file():
        raise FileNotFoundError(f"Missing required source file: {path}")
    if path.suffixes[-2:] != [".csv", ".gz"]:
        raise ValueError(f"Expected a .csv.gz source file: {path}")

    try:
        with gzip.open(path, mode="rt", encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream)
            header = tuple(next(reader))
            if header != HEADERS[table]:
                raise ValueError(f"Unexpected header in {path.name}. Expected {HEADERS[table]}, got {header}")
            row_count = sum(1 for _ in reader)
    except (gzip.BadGzipFile, EOFError) as exc:
        raise ValueError(f"Invalid gzip file: {path}") from exc

    if row_count == 0:
        raise ValueError(f"Source file contains no data rows: {path}")

    return SourceValidation(
        table=table,
        path=str(path),
        size_bytes=path.stat().st_size,
        sha256=_sha256(path),
        row_count=row_count,
    )


def validate_sources(config: IngestionConfig) -> list[SourceValidation]:
    """Validate source archives without changing their contents."""
    results = []
    for table in TABLES:
        result = _validate_file(table, config.source_dir / f"{table}.csv.gz")
        schema_path = config.schema_dir / f"{table}.json"
        if not schema_path.is_file():
            raise FileNotFoundError(f"Missing BigQuery schema: {schema_path}")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        schema_names = tuple(field["name"] for field in schema)
        if schema_names != HEADERS[table]:
            raise ValueError(f"Schema/header mismatch for {table}")
        results.append(result)
        LOGGER.info(
            "Validated %s: rows=%d bytes=%d sha256=%s",
            table,
            result.row_count,
            result.size_bytes,
            result.sha256,
        )
    return results


def _ensure_dataset(config: IngestionConfig, runner: Runner) -> None:
    destination = f"{config.project}:{config.dataset}"
    show = subprocess.run(
        ["bq", "show", "--format=json", destination],
        capture_output=True,
        text=True,
        check=False,
    )
    if show.returncode == 0:
        metadata = json.loads(show.stdout)
        actual_location = metadata.get("location", "").lower()
        if actual_location != config.location.lower():
            raise ValueError(f"Dataset {destination} is in {actual_location}, expected {config.location}")
        return
    runner(
        [
            "bq",
            "mk",
            "--dataset",
            f"--location={config.location}",
            destination,
        ]
    )


def _upload_source(
    config: IngestionConfig,
    validation: SourceValidation,
    runner: Runner,
) -> None:
    uri = config.object_uri(validation.table)
    runner(
        [
            "gcloud",
            "storage",
            "cp",
            validation.path,
            uri,
            f"--custom-metadata=source-sha256={validation.sha256}",
        ]
    )
    described = runner(
        [
            "gcloud",
            "storage",
            "objects",
            "describe",
            uri,
            "--format=json",
        ]
    )
    metadata = json.loads(described.stdout)
    if int(metadata["size"]) != validation.size_bytes:
        raise ValueError(f"Uploaded object size mismatch: {uri}")
    remote_hash = metadata.get("metadata", {}).get("source-sha256")
    if remote_hash != validation.sha256:
        raise ValueError(f"Uploaded object checksum metadata mismatch: {uri}")


def _load_bronze(
    config: IngestionConfig,
    validation: SourceValidation,
    runner: Runner,
) -> None:
    destination = f"{config.project}:{config.dataset}.{validation.table}"
    command = [
        "bq",
        "load",
        f"--project_id={config.project}",
        f"--location={config.location}",
        "--source_format=CSV",
        "--skip_leading_rows=1",
        "--allow_quoted_newlines",
        "--null_marker=",
        "--encoding=UTF-8",
    ]
    if config.replace:
        command.append("--replace")
    command.extend(
        [
            destination,
            config.object_uri(validation.table),
            str(config.schema_dir / f"{validation.table}.json"),
        ]
    )
    runner(command)

    described = runner(["bq", "show", "--format=json", destination])
    metadata = json.loads(described.stdout)
    if metadata.get("location", "").lower() != config.location.lower():
        raise ValueError(f"Bronze table location mismatch: {destination}")
    actual_fields = tuple(field["name"] for field in metadata.get("schema", {}).get("fields", []))
    if actual_fields != HEADERS[validation.table]:
        raise ValueError(f"Bronze table schema mismatch: {destination}")
    if int(metadata.get("numRows", 0)) != validation.row_count:
        raise ValueError(
            f"Row count mismatch for {destination}: expected {validation.row_count}, got {metadata.get('numRows')}"
        )


def planned_commands(
    config: IngestionConfig,
    validations: Sequence[SourceValidation],
) -> list[str]:
    commands = [f"ensure BigQuery dataset {config.project}:{config.dataset} in {config.location}"]
    for validation in validations:
        commands.append(f"upload unchanged {validation.path} -> {config.object_uri(validation.table)}")
        disposition = "replace" if config.replace else "create only"
        commands.append(
            f"load {config.object_uri(validation.table)} -> "
            f"{config.project}:{config.dataset}.{validation.table} ({disposition})"
        )
    return commands


def ingest(
    config: IngestionConfig,
    runner: Runner = default_runner,
) -> list[SourceValidation]:
    """Validate, then optionally upload raw files and load Bronze tables."""
    validations = validate_sources(config)
    if not config.apply:
        for command in planned_commands(config, validations):
            LOGGER.info("DRY RUN: %s", command)
        return validations

    _ensure_dataset(config, runner)
    for validation in validations:
        _upload_source(config, validation, runner)
        _load_bronze(config, validation, runner)
    return validations


def write_manifest(path: Path, config: IngestionConfig, results: Sequence[SourceValidation]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "project": config.project,
        "bucket": config.bucket,
        "dataset": config.dataset,
        "location": config.location,
        "version": config.version,
        "applied": config.apply,
        "files": [asdict(result) for result in results],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
