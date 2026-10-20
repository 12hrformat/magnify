import unittest

from magnify.usernames import generate


class TestUsernames(unittest.TestCase):
    def test_basic_variants(self):
        out = generate("John Doe")
        self.assertIn("johndoe", out)
        self.assertIn("john.doe", out)
        self.assertIn("john_doe", out)
        self.assertIn("john-doe", out)
        self.assertIn("doejohn", out)
        self.assertIn("jdoe", out)
        self.assertIn("jd", out)
        self.assertIn("john", out)
        self.assertIn("doe", out)

    def test_ordering_prioritizes_common(self):
        out = generate("John Doe")
        self.assertEqual(out[0], "johndoe")

    def test_single_name(self):
        out = generate("plato")
        self.assertIn("plato", out)

    def test_empty(self):
        self.assertEqual(generate(""), [])
        self.assertEqual(generate("   "), [])

    def test_dedupe_and_limit(self):
        out = generate("John Doe", limit=10)
        self.assertEqual(len(out), len(set(out)))
        self.assertLessEqual(len(out), 10)

    def test_leet_present(self):
        out = generate("alice smith")
        self.assertTrue(any(any(c in v for c in "4@3105$7")
                            and v.isalnum() and v not in ("alice", "smith")
                            for v in out))


if __name__ == "__main__":
    unittest.main()
