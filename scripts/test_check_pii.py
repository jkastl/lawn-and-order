#!/usr/bin/env python3
"""Tests for check_pii.py. All "PII" here is fake. Run: python3 scripts/test_check_pii.py"""
import os
import sys
import unittest

os.environ["PII_DENYLIST"] = "Quentin Placeholder\nfakestreet"
sys.path.insert(0, os.path.dirname(__file__))
import check_pii as c  # noqa: E402


def hits(text):
    return c.scan_text("t", text)


class Catches(unittest.TestCase):
    def test_email(self):
        self.assertTrue(hits("reach me at someone.fake@gmail.com"))  # pii-ok

    def test_phone(self):
        for s in ["call 507-555-0142", "(507) 555-0142", "+1 507.555.0142"]:  # pii-ok
            self.assertTrue(hits(s), s)

    def test_street(self):
        for s in ["1234 Elm St", "1234 14th Ave SW", "56 N Maple Lane", "2105 Fakehill Dr NW"]:  # pii-ok
            self.assertTrue(hits(s), s)

    def test_coordinates_and_parcel(self):
        self.assertTrue(hits("at 44.01234, -92.48021"))  # pii-ok
        self.assertTrue(hits("PIN 74.35.21.012345"))  # pii-ok

    def test_links(self):
        self.assertTrue(hits("https://maps.app.goo.gl/abc123"))  # pii-ok
        self.assertTrue(hits("https://www.zillow.com/homedetails/x"))  # pii-ok

    def test_denylist(self):
        self.assertTrue(hits("Copyright 2026 quentin placeholder"))  # pii-ok
        self.assertTrue(hits("on FakeStreet"))  # pii-ok

    def test_files(self):
        self.assertTrue(c.scan_blob("budget.xlsx", b"PK\x03\x04"))
        self.assertTrue(c.scan_blob("yard.jpg", b"\xff\xd8\xff\xe1\x00\x10Exif\x00\x00MM"))
        self.assertFalse(c.scan_blob("clean.png", b"\x89PNG\r\n\x1a\nIHDR"))

    def test_commit_trailer(self):
        self.assertTrue(c.check_message("m", "x\n\nCo-authored-by: A <someone.fake@gmail.com>"))  # pii-ok
        self.assertFalse(c.check_message("m", "x\n\nCo-Authored-By: Claude <noreply@anthropic.com>"))

    def test_commit_email_allowlist(self):
        self.assertTrue(c.ALLOWED_COMMIT_EMAIL.match("6042589+jkastl@users.noreply.github.com"))
        self.assertTrue(c.ALLOWED_COMMIT_EMAIL.match("41898282+github-actions[bot]@users.noreply.github.com"))
        self.assertFalse(c.ALLOWED_COMMIT_EMAIL.match("someone@gmail.com"))  # pii-ok


class Ignores(unittest.TestCase):
    def test_plan_text(self):
        for s in [
            "Rochester amended its Tall Grass and Weeds ordinance (Code 8-5) in July 2024",
            "About 7,700 sq ft, roughly 68 ft of frontage × 114 ft deep",
            "Seed ~265 sq ft at ~5 lb per 1,000 sq ft",
            "Minn. Stat. 412.925 (2023)",
            "Spacing: 10 ft from driveways, 20 ft from poles, 35 ft from an existing large boulevard tree",
            "https://rochestermn.gov/home/showpublisheddocument/26475/638538667418530000",
            "Co-Authored-By: Claude <noreply@anthropic.com>",
            "Apply Oct 1–Dec 31 for 2027 installs",
            "2 Boulevard bee lawn",
            "3 ft path along the house",
            "the wing's SW corner",
        ]:
            self.assertFalse(hits(s), s)

    def test_marker(self):
        self.assertFalse(hits("1234 Elm St pii-ok"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
