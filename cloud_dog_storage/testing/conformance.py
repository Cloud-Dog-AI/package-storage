"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: Reusable conformance suite for any StorageBackend implementation.
Standard: PS-85 (Storage Interfaces)
**************************************************
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

from cloud_dog_storage.errors import NotSupportedError

if TYPE_CHECKING:
    from cloud_dog_storage.backends.base import StorageBackend


@dataclass(frozen=True)
class ConformanceResult:
    """Result entry for a conformance test case."""

    name: str
    passed: bool
    message: str = ""


def _execute_case(name: str, func, *, skip_unsupported: bool) -> ConformanceResult:  # type: ignore[no-untyped-def]
    try:
        func()
        return ConformanceResult(name=name, passed=True)
    except NotSupportedError as exc:
        if skip_unsupported:
            return ConformanceResult(name=name, passed=True, message=f"skipped: {exc}")
        return ConformanceResult(name=name, passed=False, message=str(exc))
    except Exception as exc:
        return ConformanceResult(name=name, passed=False, message=str(exc))


def run_conformance_suite(backend: StorageBackend, *, skip_unsupported: bool = True) -> list[ConformanceResult]:
    """Run a compact conformance suite against any backend instance."""
    base = "/cloud_dog_test_conformance"
    src = f"{base}/a.txt"
    dst = f"{base}/b.txt"
    moved = f"{base}/c.txt"

    def _setup() -> None:
        # Some backends (e.g., S3) have no directory semantics. Treat create_dir as optional.
        with contextlib.suppress(NotSupportedError):
            backend.create_dir(base, parents=True, exist_ok=True)
        backend.write_bytes(src, b"hello", overwrite=True)

    def _read_round_trip() -> None:
        data = backend.read_bytes(src)
        assert data == b"hello"

    def _overwrite() -> None:
        backend.write_bytes(src, b"bye", overwrite=True)
        assert backend.read_bytes(src) == b"bye"

    def _copy_move() -> None:
        backend.copy_path(src, dst, overwrite=True)
        assert backend.read_bytes(dst) == b"bye"
        backend.move_path(dst, moved, overwrite=True)
        assert backend.exists(moved)

    def _list_stat_delete() -> None:
        entries = backend.list_dir(base, recursive=True)
        assert any(item.path.endswith("a.txt") for item in entries)
        stat = backend.stat(src)
        assert stat is not None
        backend.delete_path(moved, missing_ok=True)
        backend.delete_path(src, missing_ok=False)
        # Deleting a directory is backend-dependent; treat as optional.
        with contextlib.suppress(NotSupportedError):
            backend.delete_path(base, missing_ok=True)

    cases = [
        ("setup", _setup),
        ("read_round_trip", _read_round_trip),
        ("overwrite", _overwrite),
        ("copy_move", _copy_move),
        ("list_stat_delete", _list_stat_delete),
    ]
    return [_execute_case(name, fn, skip_unsupported=skip_unsupported) for name, fn in cases]
