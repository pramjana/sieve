"""Tests for export: GET /export/{fmt} downloads the current view —
filt()'s rows (search + column filters + text filters) restricted to the
view columns (title, sub, detail, deduped) — as CSV or Excel.
"""

import csv
import io
import unittest

import pandas as pd
from starlette.testclient import TestClient

import app


class ExportTests(unittest.TestCase):
    def setUp(self):
        frame = pd.DataFrame({
            "Name": ["Alpha", "Beta", "Gamma"],
            "Note": ["red apple", "blue", "red sky"],
            "Category": ["fruit", "color", "weather"],
        }).reset_index(drop=True)
        app.S.update(
            df=frame, all_dfs={"Sheet1": frame}, sheets=["Sheet1"],
            sheet="Sheet1", filename="demo.csv", cols=list(frame.columns),
            tc="Name", sc="Note", dc=list(frame.columns), fc=list(frame.columns),
            flt={}, ft={}, search="", sel=None, error=None, view_restored=False,
        )
        self.client = TestClient(app.app)
        self.htmx = {"HX-Request": "true"}

    def csv_rows(self, response):
        rows = list(csv.reader(io.StringIO(response.content.decode("utf-8-sig"))))
        return rows[0], rows[1:]

    # ── CSV ────────────────────────────────────────────────────────────
    def test_csv_export_all_rows_in_view_column_order(self):
        app.S.update(tc="Category", sc="Name", dc=["Note"])
        response = self.client.get("/export/csv")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["content-type"].startswith("text/csv"))
        header, rows = self.csv_rows(response)
        self.assertEqual(header, ["Category", "Name", "Note"])  # tc, sc, dc
        self.assertEqual(len(rows), 3)

    def test_csv_export_applies_filters_and_search(self):
        app.S.update(search="red")
        _, rows = self.csv_rows(self.client.get("/export/csv"))
        self.assertEqual([r[0] for r in rows], ["Alpha", "Gamma"])
        app.S.update(flt={"Category": {"fruit"}})
        _, rows = self.csv_rows(self.client.get("/export/csv"))
        self.assertEqual([r[0] for r in rows], ["Alpha"])  # search AND filter
        app.S.update(ft={"Note": "sky"})
        _, rows = self.csv_rows(self.client.get("/export/csv"))
        self.assertEqual(rows, [])
        self.assertIn("0 filtered rows", self.client.get("/").text)

    def test_csv_export_dedupes_title_sub_detail_overlap(self):
        app.S.update(tc="Name", sc="Name", dc=["Name", "Note"])
        header, _ = self.csv_rows(self.client.get("/export/csv"))
        self.assertEqual(header, ["Name", "Note"])

    # ── Excel ──────────────────────────────────────────────────────────
    def test_xlsx_export_round_trip(self):
        app.S.update(dc=["Name", "Note"])
        response = self.client.get("/export/xlsx")
        self.assertEqual(response.status_code, 200)
        self.assertIn("spreadsheetml", response.headers["content-type"])
        back = pd.read_excel(io.BytesIO(response.content))
        self.assertEqual(list(back.columns), ["Name", "Note"])
        self.assertEqual(len(back), 3)
        self.assertEqual(back["Name"].tolist(), ["Alpha", "Beta", "Gamma"])

    def test_xlsx_export_respects_filters(self):
        app.S.update(flt={"Category": {"color"}})
        back = pd.read_excel(io.BytesIO(self.client.get("/export/xlsx").content))
        self.assertEqual(back["Name"].tolist(), ["Beta"])

    # ── edge cases ─────────────────────────────────────────────────────
    def test_unknown_format_is_404(self):
        self.assertEqual(self.client.get("/export/pdf").status_code, 404)

    def test_export_without_file_redirects_home(self):
        app.S["df"] = None
        response = self.client.get("/export/csv", follow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], "/")

    def test_content_disposition_filename_is_sanitized(self):
        app.S["filename"] = "we/ird &na\"me.xlsx"
        app.S["sheet"] = "S 1"
        cd = self.client.get("/export/csv").headers["content-disposition"]
        self.assertIn("attachment", cd)
        name = cd.split("filename*=UTF-8''", 1)[1]
        self.assertNotIn("/", name)
        self.assertNotIn('"', name)
        self.assertTrue(name.endswith(".csv"))
        self.assertIn("na_me", name)  # & and " replaced with _
        self.assertIn("S", name)

    def test_sidebar_shows_export_links(self):
        html = self.client.get("/").text
        self.assertIn('href="/export/csv"', html)
        self.assertIn('href="/export/xlsx"', html)
        self.assertIn("3 filtered rows", html)


if __name__ == "__main__":
    unittest.main()
