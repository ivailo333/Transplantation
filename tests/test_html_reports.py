import unittest

import html_reports


class TestHtmlReports(unittest.TestCase):

    def test_table_escapes_values(self):
        html = html_reports.render_table(
            (("name", "Name"),),
            [{"name": "A&B <test>"}],
        )
        self.assertIn("A&amp;B &lt;test&gt;", html)

    def test_page_contains_sections_and_notice(self):
        html = html_reports.render_page(
            "Title",
            (("Mode", "TEST"),),
            (("Section", "<p>Body</p>"),),
            "NON-CLINICAL",
        )
        self.assertIn("<h1>Title</h1>", html)
        self.assertIn("<h2>Section</h2>", html)
        self.assertIn("NON-CLINICAL", html)


if __name__ == "__main__":
    unittest.main()
