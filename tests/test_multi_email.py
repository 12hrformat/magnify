"""Multi-email target tests."""

import unittest

from magnify.dorks import DorkConfig, build
from magnify.session import Target


class TestTargetEmails(unittest.TestCase):
    def test_parse_spaces(self):
        self.assertEqual(Target.parse_emails("a@x.com b@y.com"),
                         ["a@x.com", "b@y.com"])

    def test_parse_commas(self):
        self.assertEqual(Target.parse_emails("a@x.com, b@y.com"),
                         ["a@x.com", "b@y.com"])

    def test_parse_mixed_and_dedupes(self):
        self.assertEqual(Target.parse_emails("a@x.com,b@y.com a@x.com"),
                         ["a@x.com", "b@y.com"])

    def test_parse_empty(self):
        self.assertEqual(Target.parse_emails(""), [])
        self.assertEqual(Target.parse_emails("   "), [])

    def test_primary_from_list(self):
        t = Target(emails=["a@x.com", "b@y.com"])
        self.assertEqual(t.email, "a@x.com")
        self.assertEqual(t.emails, ["a@x.com", "b@y.com"])

    def test_list_from_primary(self):
        t = Target(email="a@x.com")
        self.assertEqual(t.emails, ["a@x.com"])

    def test_primary_not_duplicated_in_list(self):
        t = Target(email="a@x.com", emails=["a@x.com", "b@y.com"])
        self.assertEqual(t.emails, ["a@x.com", "b@y.com"])

    def test_empty_detects_no_fields(self):
        self.assertTrue(Target().empty())
        self.assertFalse(Target(emails=["a@x.com"]).empty())


class TestMultiEmailDorks(unittest.TestCase):
    def test_leak_battery_covers_every_address(self):
        cfg = DorkConfig(include_leaks=True)
        out = build(Target(emails=["a@x.com", "b@y.com"]), cfg)
        self.assertTrue(any("a@x.com" in d for d in out))
        self.assertTrue(any("b@y.com" in d for d in out))

    def test_each_address_gets_full_battery(self):
        cfg = DorkConfig(include_leaks=True)
        out = build(Target(emails=["a@x.com", "b@y.com"]), cfg)
        a = [d for d in out if "a@x.com" in d]
        b = [d for d in out if "b@y.com" in d]
        self.assertEqual(len(a), len(b))
        self.assertGreater(len(a), 1)

    def test_local_part_pairs_with_its_own_domain(self):
        """b@y.com must not produce '"b" "x.com"'."""
        cfg = DorkConfig(include_leaks=True)
        out = build(Target(emails=["a@x.com", "b@y.com"]), cfg)
        self.assertIn('"a" "x.com" (confidential OR internal)', out)
        self.assertIn('"b" "y.com" (confidential OR internal)', out)
        self.assertNotIn('"a" "y.com" (confidential OR internal)', out)

    def test_no_duplicate_dorks(self):
        cfg = DorkConfig(include_leaks=True)
        out = build(Target(emails=["a@x.com", "a@x.com"]), cfg)
        self.assertEqual(len(out), len(set(out)))

    def test_single_email_still_works(self):
        cfg = DorkConfig(include_leaks=True)
        out = build(Target(email="a@x.com"), cfg)
        self.assertTrue(any("a@x.com" in d for d in out))


if __name__ == "__main__":
    unittest.main()
