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


class TestStep13BInteractiveId(unittest.TestCase):

    def test_prompt_external_id_strips_outer_spaces(self):
        result = hla.prompt_external_id(
            "DONOR",
            input_func=lambda prompt: "  DONOR-001  ",
            output_func=lambda message: None,
        )
        self.assertEqual(result, "DONOR-001")

    def test_prompt_external_id_retries_empty_value(self):
        values = iter(["   ", "DONOR-001"])
        output = []

        result = hla.prompt_external_id(
            "DONOR",
            input_func=lambda prompt: next(values),
            output_func=output.append,
        )

        self.assertEqual(result, "DONOR-001")
        self.assertTrue(any("ERROR:" in line for line in output))

    def test_prompt_external_id_q_cancels(self):
        with self.assertRaises(hla.InputCancelled):
            hla.prompt_external_id(
                "DONOR",
                input_func=lambda prompt: "q",
                output_func=lambda message: None,
            )
