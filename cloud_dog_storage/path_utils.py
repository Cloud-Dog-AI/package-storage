"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: Platform path utilities replacing bespoke Path/PurePosixPath usage.
Standard: PS-85 (Storage Interfaces)
**************************************************
"""

from __future__ import annotations

import os
import posixpath
import shutil
from pathlib import Path, PurePosixPath
from typing import Iterable


def resolve_path(path: str) -> str:
    """Expand user home and resolve to an absolute canonical path string."""
    return str(Path(path).expanduser().resolve())


def resolve_strict(path: str) -> str:
    """Resolve path strictly, raising FileNotFoundError if it does not exist."""
    return str(Path(path).resolve(strict=True))


def to_posix(path: str) -> str:
    """Return the POSIX string representation of a path."""
    return Path(path).as_posix()


def suffix(path: str) -> str:
    """Return the file extension (e.g. '.txt') from a path string."""
    return PurePosixPath(path).suffix


def name(path: str) -> str:
    """Return the final component of a path."""
    return PurePosixPath(path).name


def parent(path: str) -> str:
    """Return the logical parent directory of a path."""
    return str(PurePosixPath(path).parent)


def relative_to(path: str, base: str) -> str:
    """Return path relative to base, raising ValueError if not relative."""
    return str(PurePosixPath(path).relative_to(PurePosixPath(base)))


def relative_parts(path: str, base: str) -> tuple[str, ...]:
    """Return the parts of path relative to base."""
    return PurePosixPath(path).relative_to(PurePosixPath(base)).parts


def match_glob(path: str, pattern: str) -> bool:
    """Test whether path matches a glob pattern."""
    return PurePosixPath(path).match(pattern)


def posix_path(path: str) -> str:
    """Normalise a path string to absolute POSIX form."""
    p = PurePosixPath(path if path else "/")
    if not str(p).startswith("/"):
        p = PurePosixPath("/") / p
    return str(PurePosixPath(posixpath.normpath(str(p))))


def expand_user(path: str) -> str:
    """Expand the user home directory prefix in a path."""
    return str(Path(path).expanduser())


def join_paths(*parts: str) -> str:
    """Join path segments, resolving to an absolute path."""
    return str(Path(*parts).resolve())


def is_absolute(path: str) -> bool:
    """Return whether the path is absolute."""
    return PurePosixPath(path).is_absolute()


def normalize_posix(path: str) -> str:
    """Normalise a POSIX path string (collapse .., ., etc)."""
    return posixpath.normpath(path)


def cwd() -> str:
    """Return the current working directory as a string."""
    return str(Path.cwd())


def disk_usage(path: str) -> tuple[int, int, int]:
    """Return (total, used, free) bytes for the filesystem containing path.

    Wraps shutil.disk_usage.
    """
    usage = shutil.disk_usage(path)
    return (usage.total, usage.used, usage.free)


def file_uri(path: str) -> str:
    """Return a file:// URI for a path."""
    return Path(path).resolve().as_uri()


def is_relative_to(path: str, base: str) -> bool:
    """Return True if path is relative to base."""
    try:
        PurePosixPath(path).relative_to(PurePosixPath(base))
        return True
    except ValueError:
        return False


def iter_dir(path: str) -> list[str]:
    """List immediate children of a directory as path strings."""
    return [str(child) for child in sorted(Path(path).iterdir())]


def walk(root: str) -> Iterable[tuple[str, list[str], list[str]]]:
    """Walk a directory tree, yielding (dirpath, dirnames, filenames) as strings."""
    for dirpath, dirnames, filenames in os.walk(root):
        yield (dirpath, dirnames, filenames)


def rglob(root: str, pattern: str) -> list[str]:
    """Recursively glob under root, returning matching path strings."""
    return [str(p) for p in Path(root).rglob(pattern)]


def read_link(path: str) -> str:
    """Read the target of a symbolic link."""
    return os.readlink(path)


def exists(path: str) -> bool:
    """Return whether a path exists on the filesystem."""
    return Path(path).exists()


def is_file(path: str) -> bool:
    """Return whether a path is a file."""
    return Path(path).is_file()


def is_dir(path: str) -> bool:
    """Return whether a path is a directory."""
    return Path(path).is_dir()


def file_stat(path: str) -> os.stat_result:
    """Return os.stat_result for a path."""
    return Path(path).stat()


def read_text(path: str, *, encoding: str = "utf-8", errors: str | None = None) -> str:
    """Read file content as text."""
    if errors is not None:
        with open(path, "r", encoding=encoding, errors=errors) as fh:
            return fh.read()
    return Path(path).read_text(encoding=encoding)


def read_bytes(path: str) -> bytes:
    """Read file content as bytes."""
    return Path(path).read_bytes()


def write_text(path: str, content: str, *, encoding: str = "utf-8") -> None:
    """Write text content to a file."""
    Path(path).write_text(content, encoding=encoding)


def write_bytes(path: str, data: bytes) -> None:
    """Write binary content to a file."""
    Path(path).write_bytes(data)


def mkdir(path: str, *, parents: bool = True, exist_ok: bool = True) -> None:
    """Create a directory, optionally creating parents."""
    Path(path).mkdir(parents=parents, exist_ok=exist_ok)


def copy_with_metadata(src: str, dst: str) -> str:
    """Copy a file preserving metadata (timestamps, permissions) via shutil.copy2.

    Parent directories of dst are created automatically.
    Returns the destination path string.
    """
    dst_path = Path(dst)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst


def as_path(path: str | object) -> "Path":
    """Convert a string or path-like to a pathlib.Path.
    
    Use this when interfacing with APIs that require Path objects.
    Prefer string-based path_utils functions for new code.
    """
    from pathlib import Path as _Path
    return _Path(str(path))


def join(*parts: str) -> str:
    """Join path components. Platform replacement for os.path.join."""
    import os.path
    return os.path.join(*parts)


def rmtree(path: str, *, ignore_errors: bool = True) -> None:
    """Remove directory tree. Platform replacement for shutil.rmtree."""
    shutil.rmtree(str(path), ignore_errors=ignore_errors)


def move(src: str, dst: str) -> str:
    """Move file or directory. Platform replacement for shutil.move."""
    return str(shutil.move(str(src), str(dst)))
