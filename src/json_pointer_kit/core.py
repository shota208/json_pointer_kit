"""Core RFC 6901 JSON Pointer implementation.

Only the standard library is used.  The functions here operate on plain Python
objects (dicts, lists, strings, ints, floats, bools, None) and raise
``JsonPointerError`` for malformed pointers or missing paths.

Decisions worth calling out:

* ``resolve`` returns the value at the pointer and raises ``JsonPointerError``
  when the path does not exist.  There is no ``default`` argument: a caller that
  wants a fallback can catch the exception, and a caller that wants to
  distinguish "missing" from "present but None" gets that distinction for free.
* ``apply`` mutates the document in place.  JSON Pointer is a path language, and
  the only way to make a path write meaningful is to write into the container
  that owns the final token.  Returning a new document would require copying
  every ancestor and would silently break aliasing that callers may rely on.
* Array indices are accepted as decimal strings only.  ``"01"`` is rejected
  because RFC 6901 section 4 says array indices are ``0`` or ``[1-9][0-9]*``.
  Rejecting it here is cheaper than letting ``int()`` accept it and then
  wondering why ``/a/01`` and ``/a/1`` disagree.
* The ``-`` token is only meaningful for ``apply`` on an array, where it means
  "append".  For ``resolve`` it is treated like any other non-numeric token and
  therefore fails on an array; that matches the RFC's statement that ``-``
  refers to the nonexistent element after the last one.
"""

from __future__ import annotations

from typing import Any, List, Union

__all__ = ["JsonPointerError", "resolve", "apply"]


class JsonPointerError(ValueError):
    """Raised for malformed pointers and for paths that do not exist."""


# A token is always a string; the parsed pointer is a list of tokens.
def _parse(pointer: str) -> List[str]:
    if not isinstance(pointer, str):
        raise JsonPointerError("pointer must be a string")
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise JsonPointerError("pointer must be empty or start with '/': %r" % (pointer,))
    # split('/') on "/a/b" yields ['', 'a', 'b']; drop the leading empty piece.
    return [_unescape(token) for token in pointer[1:].split("/")]


def _unescape(token: str) -> str:
    # RFC 6901 order matters: ~1 must be replaced before ~0, otherwise the
    # sequence ~01 would be read as ~0 followed by 1 and become '~1' instead
    # of the intended '~' followed by '1'.
    return token.replace("~1", "/").replace("~0", "~")


def _escape(token: str) -> str:
    return token.replace("~", "~0").replace("/", "~1")


def _is_array_index(token: str) -> bool:
    """True for tokens that RFC 6901 allows as array indices."""
    if token == "0":
        return True
    if not token:
        return False
    if token[0] == "0":
        return False
    return token.isdigit()


def _lookup(document: Any, token: str) -> Any:
    if isinstance(document, dict):
        if token not in document:
            raise JsonPointerError("key not found: %r" % (token,))
        return document[token]
    if isinstance(document, list):
        if not _is_array_index(token):
            raise JsonPointerError("not a valid array index: %r" % (token,))
        index = int(token)
        if index >= len(document):
            raise JsonPointerError("array index out of range: %d" % (index,))
        return document[index]
    raise JsonPointerError("cannot index %s with %r" % (type(document).__name__, token))


def resolve(document: Any, pointer: str) -> Any:
    """Return the value that ``pointer`` refers to inside ``document``.

    Raises ``JsonPointerError`` if the pointer is malformed or the path does
    not exist.  An empty pointer returns ``document`` unchanged.
    """
    current = document
    for token in _parse(pointer):
        current = _lookup(current, token)
    return current


def _set(document: Any, token: str, value: Any) -> None:
    if isinstance(document, dict):
        document[token] = value
        return
    if isinstance(document, list):
        if token == "-":
            document.append(value)
            return
        if not _is_array_index(token):
            raise JsonPointerError("not a valid array index: %r" % (token,))
        index = int(token)
        if index > len(document):
            raise JsonPointerError("array index out of range: %d" % (index,))
        if index == len(document):
            document.append(value)
        else:
            document[index] = value
        return
    raise JsonPointerError("cannot assign into %s" % (type(document).__name__))


def apply(document: Any, pointer: str, value: Any) -> Any:
    """Write ``value`` at ``pointer`` inside ``document`` and return ``document``.

    The document is mutated in place.  The final token is assigned into its
    parent container; intermediate tokens must already exist.  For arrays the
    special token ``-`` appends, and an index equal to the array length also
    appends (matching the RFC's description of the element after the last one).
    """
    tokens = _parse(pointer)
    if not tokens:
        raise JsonPointerError("cannot apply to the empty pointer")
    parent = document
    for token in tokens[:-1]:
        parent = _lookup(parent, token)
    _set(parent, tokens[-1], value)
    return document


def escape(token: str) -> str:
    """Escape a single reference token for embedding in a pointer."""
    return _escape(token)


def unescape(token: str) -> str:
    """Undo :func:`escape` for a single reference token."""
    return _unescape(token)
