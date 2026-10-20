import unittest

from magnify import emailintel


class TestEmailIntel(unittest.TestCase):
    def test_syntax(self):
        self.assertTrue(emailintel.valid_syntax("john@example.com"))
        self.assertTrue(emailintel.valid_syntax("j.doe+tag@sub.example.co.uk"))
        self.assertFalse(emailintel.valid_syntax("not-an-email"))
        self.assertFalse(emailintel.valid_syntax("no@tld"))
        self.assertFalse(emailintel.valid_syntax("@example.com"))

    def test_invalid_syntax_short_circuits(self):
        findings = emailintel.lookup("garbage")
        self.assertIn("error", findings)

    def test_provider_map(self):
        self.assertEqual(emailintel.PROVIDER_MAP.get("gmail.com"),
                         "Google Gmail")
        self.assertEqual(emailintel.PROVIDER_MAP.get("proton.me"),
                         "Proton Mail")

    def test_disposable(self):
        self.assertIn("mailinator.com", emailintel.DISPOSABLE_DOMAINS)
        self.assertNotIn("example.com", emailintel.DISPOSABLE_DOMAINS)

    def test_summarize_handles_error(self):
        lines = emailintel.summarize({"error": "invalid email syntax"})
        self.assertEqual(len(lines), 1)


if __name__ == "__main__":
    unittest.main()
