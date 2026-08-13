#!/usr/bin/env python3
"""Cross-platform hashing policy for FIN-C3 release artifacts."""

from __future__ import annotations

import hashlib
from pathlib import Path


TEXT_SUFFIXES = frozenset({".csv", ".sql", ".tmdl"})
TEXT_HASH_MODE = "utf-8-canonical-lf"
BINARY_HASH_MODE = "exact-bytes"


def artifact_payload(path: Path) -> tuple[bytes, str]:
    """Return the bytes covered by the release hash and its declared mode."""
    raw = path.read_bytes()
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return raw, BINARY_HASH_MODE

    text = raw.decode("utf-8")
    canonical = text.replace("\r\n", "\n").replace("\r", "\n")
    return canonical.encode("utf-8"), TEXT_HASH_MODE


def artifact_metadata(path: Path) -> dict[str, int | str]:
    payload, mode = artifact_payload(path)
    return {
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "hash_mode": mode,
    }


def artifact_sha256(path: Path, *, uppercase: bool = False) -> str:
    digest = artifact_metadata(path)["sha256"]
    return digest.upper() if uppercase else digest
