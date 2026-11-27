"""Resolve and apply RFC 6901 JSON Pointers.

This package exposes a small, dependency-free implementation of JSON Pointer
resolution and application.  The public API is re-exported here so callers can
write ``from json_pointer_kit import resolve`` without reaching into the
submodule.
"""

from .core import apply, resolve

__all__ = ["apply", "resolve"]
