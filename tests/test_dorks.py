import unittest

from magnify.dorks import DorkConfig, build
from magnify.session import Target


class TestDorks(unittest.TestCase):
    def test_empty_target(self):
        self.assertEqual(build(Target(), DorkConfig()), [])

    def test_name_pdf_battery(self):
        cfg = DorkConfig(filetypes=["pdf"], include_leaks=False)
        out = build(Target(name="John Doe"), cfg)
        self.assertTrue(any("filetype:pdf" in d and '"John Doe"' in d
                            for d in out))

    def test_site_pick(self):
        cfg = DorkConfig(sites=["linkedin.com/in"], include_leaks=False)
        out = build(Target(name="John Doe"), cfg)
        self.assertTrue(any("site:linkedin.com/in" in d for d in out))

    def test_leak_battery_uses_email(self):
        cfg = DorkConfig()
        out = build(Target(email="john@example.com"), cfg)
        self.assertTrue(any("john@example.com" in d and "password" in d
                            for d in out))

    def test_no_leaks_without_email(self):
        cfg = DorkConfig()
        out = build(Target(name="John Doe"), cfg)
        self.assertFalse(any("password" in d for d in out))

    def test_domain_recon(self):
        cfg = DorkConfig(include_leaks=False)
        out = build(Target(domain="example.com"), cfg)
        self.assertTrue(any("site:example.com" in d for d in out))

    def test_email_provider_never_used_as_site_domain(self):
        """Regression: an email must not cause site:gmail.com dorks."""
        cfg = DorkConfig(modifiers=["intitle:index of"], include_leaks=True)
        out = build(Target(email="testuser@example.com"), cfg)
        self.assertFalse(any("site:gmail.com" in d for d in out),
                         f"leaked provider dorks: {out}")

    def test_email_still_powers_leak_battery(self):
        cfg = DorkConfig(modifiers=["intitle:index of"], include_leaks=True)
        out = build(Target(email="testuser@example.com"), cfg)
        self.assertTrue(any("testuser@example.com" in d for d in out))
        self.assertTrue(any('"testuser" "gmail.com"' in d for d in out))

    def test_real_domain_still_generates_index_dorks(self):
        cfg = DorkConfig(modifiers=["intitle:index of"], include_leaks=False)
        out = build(Target(domain="acme-corp.com"), cfg)
        self.assertTrue(any('site:acme-corp.com intitle:"index of"' in d
                            for d in out))

    def test_dedupe(self):
        cfg = DorkConfig(filetypes=["pdf", "pdf"], include_leaks=False)
        out = build(Target(name="John Doe"), cfg)
        self.assertEqual(len(out), len(set(out)))


if __name__ == "__main__":
    unittest.main()
