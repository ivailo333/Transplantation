import copy
import csv
import json
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
import unittest
from unittest.mock import patch

import hla_match as hla
import database as database
import exporters as exporters
import migrations as migrations

from test_helpers import make_test_bundle, make_comparison_results


class TestCompareLocus(unittest.TestCase):
    """Тестове на copy-sensitive Counter логиката без зависимост от py-ard."""

    def test_full_match(self):
        result = hla.compare_locus(
            ["A*02:01", "A*24:02"],
            ["A*02:01", "A*24:02"],
        )
        self.assertEqual(result["shared_count"], 2)
        self.assertEqual(result["mismatch_count"], 0)
        self.assertEqual(result["recipient_only_count"], 0)

    def test_full_mismatch(self):
        result = hla.compare_locus(
            ["A*02:01", "A*24:02"],
            ["A*03:01", "A*26:01"],
        )
        self.assertEqual(result["shared_count"], 0)
        self.assertEqual(result["mismatch_count"], 2)
        self.assertEqual(result["recipient_only_count"], 2)

    def test_one_shared_allele(self):
        result = hla.compare_locus(
            ["A*02:01", "A*24:02"],
            ["A*02:01", "A*03:01"],
        )
        self.assertEqual(result["shared"], ["A*02:01"])
        self.assertEqual(result["donor_only"], ["A*24:02"])
        self.assertEqual(result["recipient_only"], ["A*03:01"])
        self.assertEqual(result["shared_count"], 1)
        self.assertEqual(result["mismatch_count"], 1)

    def test_homozygous_full_match(self):
        result = hla.compare_locus(
            ["A*02:01", "A*02:01"],
            ["A*02:01", "A*02:01"],
        )
        self.assertEqual(result["shared"], ["A*02:01", "A*02:01"])
        self.assertEqual(result["shared_count"], 2)
        self.assertEqual(result["mismatch_count"], 0)

    def test_homozygous_vs_heterozygous(self):
        result = hla.compare_locus(
            ["A*02:01", "A*02:01"],
            ["A*02:01", "A*24:02"],
        )
        self.assertEqual(result["shared"], ["A*02:01"])
        self.assertEqual(result["donor_only"], ["A*02:01"])
        self.assertEqual(result["recipient_only"], ["A*24:02"])
        self.assertEqual(result["shared_count"], 1)
        self.assertEqual(result["mismatch_count"], 1)
        self.assertEqual(result["recipient_only_count"], 1)

    def test_allele_order_does_not_matter(self):
        result = hla.compare_locus(
            ["A*02:01", "A*24:02"],
            ["A*24:02", "A*02:01"],
        )
        self.assertEqual(result["shared_count"], 2)
        self.assertEqual(result["mismatch_count"], 0)
        self.assertEqual(result["recipient_only_count"], 0)
