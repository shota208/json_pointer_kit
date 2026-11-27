import unittest

from json_pointer_kit import apply, resolve
from json_pointer_kit.core import JsonPointerError, escape, unescape


class ResolveTests(unittest.TestCase):
    def setUp(self):
        self.doc = {
            "foo": ["bar", "baz"],
            "": 0,
            "a/b": 1,
            "c%d": 2,
            "e^f": 3,
            "g|h": 4,
            "i\\j": 5,
            "k\"l": 6,
            " ": 7,
            "m~n": 8,
        }

    def test_empty_pointer_returns_document(self):
        self.assertIs(resolve(self.doc, ""), self.doc)

    def test_root_tokens(self):
        self.assertEqual(resolve(self.doc, "/foo"), ["bar", "baz"])
        self.assertEqual(resolve(self.doc, "/foo/0"), "bar")
        self.assertEqual(resolve(self.doc, "/foo/1"), "baz")
        self.assertEqual(resolve(self.doc, "/"), 0)

    def test_escaped_tokens(self):
        self.assertEqual(resolve(self.doc, "/a~1b"), 1)
        self.assertEqual(resolve(self.doc, "/m~0n"), 8)
        self.assertEqual(resolve(self.doc, "/ "), 7)

    def test_other_special_characters_are_literal(self):
        self.assertEqual(resolve(self.doc, "/c%d"), 2)
        self.assertEqual(resolve(self.doc, "/e^f"), 3)
        self.assertEqual(resolve(self.doc, "/g|h"), 4)
        self.assertEqual(resolve(self.doc, "/i\\j"), 5)
        self.assertEqual(resolve(self.doc, "/k\"l"), 6)

    def test_missing_key_raises(self):
        with self.assertRaises(JsonPointerError):
            resolve(self.doc, "/nope")

    def test_array_index_out_of_range_raises(self):
        with self.assertRaises(JsonPointerError):
            resolve(self.doc, "/foo/2")

    def test_leading_zero_index_is_rejected(self):
        with self.assertRaises(JsonPointerError):
            resolve(self.doc, "/foo/01")

    def test_negative_index_is_rejected(self):
        with self.assertRaises(JsonPointerError):
            resolve(self.doc, "/foo/-1")

    def test_dash_on_array_raises(self):
        with self.assertRaises(JsonPointerError):
            resolve(self.doc, "/foo/-")

    def test_pointer_must_start_with_slash(self):
        with self.assertRaises(JsonPointerError):
            resolve(self.doc, "foo")

    def test_pointer_must_be_a_string(self):
        with self.assertRaises(JsonPointerError):
            resolve(self.doc, 3)  # type: ignore[arg-type]

    def test_scalar_is_not_indexable(self):
        with self.assertRaises(JsonPointerError):
            resolve(self.doc, "/foo/0/0")


class ApplyTests(unittest.TestCase):
    def test_set_existing_key(self):
        doc = {"a": {"b": 1}}
        result = apply(doc, "/a/b", 2)
        self.assertIs(result, doc)
        self.assertEqual(doc, {"a": {"b": 2}})

    def test_add_new_key(self):
        doc = {"a": {}}
        apply(doc, "/a/b", 1)
        self.assertEqual(doc, {"a": {"b": 1}})

    def test_replace_array_element(self):
        doc = {"a": [1, 2, 3]}
        apply(doc, "/a/1", 9)
        self.assertEqual(doc, {"a": [1, 9, 3]})

    def test_append_with_dash(self):
        doc = {"a": [1, 2]}
        apply(doc, "/a/-", 3)
        self.assertEqual(doc, {"a": [1, 2, 3]})

    def test_append_with_index_equal_to_length(self):
        doc = {"a": [1, 2]}
        apply(doc, "/a/2", 3)
        self.assertEqual(doc, {"a": [1, 2, 3]})

    def test_index_beyond_length_raises(self):
        doc = {"a": [1, 2]}
        with self.assertRaises(JsonPointerError):
            apply(doc, "/a/5", 3)

    def test_missing_intermediate_raises(self):
        doc = {"a": {}}
        with self.assertRaises(JsonPointerError):
            apply(doc, "/a/b/c", 1)

    def test_empty_pointer_is_rejected(self):
        doc = {"a": 1}
        with self.assertRaises(JsonPointerError):
            apply(doc, "", 2)

    def test_apply_into_scalar_raises(self):
        doc = {"a": 1}
        with self.assertRaises(JsonPointerError):
            apply(doc, "/a/b", 2)

    def test_escaped_key_is_used_literally(self):
        doc = {"a/b": {}}
        apply(doc, "/a~1b/c", 1)
        self.assertEqual(doc, {"a/b": {"c": 1}})


class EscapeTests(unittest.TestCase):
    def test_escape_and_unescape_round_trip(self):
        for token in ["", "a", "a/b", "m~n", "~1", "~0", "/"]:
            escaped = escape(token)
            self.assertEqual(unescape(escaped), token)

    def test_escape_order(self):
        # A literal tilde must become ~0 before slashes become ~1, otherwise
        # the ~ in ~1 would be doubled by a later pass.
        self.assertEqual(escape("~/~"), "~0~1~0")

    def test_unescape_order(self):
        # ~01 must decode as ~1, not as /.
        self.assertEqual(unescape("~01"), "~1")


if __name__ == "__main__":
    unittest.main()
