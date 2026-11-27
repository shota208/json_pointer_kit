# json_pointer_kit

Resolve and apply RFC 6901 JSON Pointers against plain Python objects.

```python
from json_pointer_kit import apply, resolve

user = {
    "name": "Ada",
    "roles": ["admin", "editor"],
    "profile": {"email": "ada@example.org"},
}

assert resolve(user, "/name") == "Ada"
assert resolve(user, "/roles/1") == "editor"
assert resolve(user, "/profile/email") == "ada@example.org"

apply(user, "/roles/-", "viewer")
assert user["roles"] == ["admin", "editor", "viewer"]

apply(user, "/profile/email", "ada@new.example.org")
assert user["profile"]["email"] == "ada@new.example.org"
```

The public names are `resolve`, `apply`, and `JsonPointerError` (plus the
`escape` and `unescape` helpers for building pointers from raw keys).  They are
re-exported from the package root, so `from json_pointer_kit import resolve` is
the intended import style.

## Why this exists

JSON Pointer is small enough that people often inline it, and then discover the
edge cases one by one: `~1` versus `~0` ordering, `"01"` not being the same as
`"1"`, and the fact that a pointer with no leading slash is not a pointer at
all.  This package is a single, tested implementation of those rules.

The main trade-off is that `apply` mutates the document in place instead of
returning a copy.  A path language is only useful if you can write through it,
and writing through a path means touching the container that owns the last
token.  Copying every ancestor would break aliasing that callers may rely on
and would make the common case (update a field in a config dict) allocate far
more than it needs to.  If you want a copy, deep-copy the document yourself
before calling `apply`.

## The awkward edge

Array indices are strict.  RFC 6901 allows `0` or `[1-9][0-9]*`, so `"/roles/01"`
is rejected rather than silently treated as index 1.  The special token `-`
means "the element after the last one" and is only accepted by `apply`, where
it appends; `resolve` treats it as a normal (and therefore missing) key.

## Testing

```
PYTHONPATH=src python -m unittest discover -s tests
```
