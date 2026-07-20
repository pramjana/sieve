"""Regression tests for state-consistency fixes (code-review-kimi.md).

Covers:
- P1-3: detail pane resets out-of-band when the selected row is filtered out
- P1-6: /cfg returns an OOB rebuild of the sidebar column filters
- Upload / sheet-switch / close round-trips keep global state coherent
- /clear-error dismisses an upload error without wiping a loaded file
"""

import unittest

import pandas as pd
from starlette.testclient import TestClient

import app


class StateConsistencyTests(unittest.TestCase):
    def setUp(self):
        frame = pd.DataFrame({
            "Name": ["Alpha", "Beta", "Gamma"],
            "Note": ["red apple", "blue", "red sky"],
            "Category": ["fruit", "color", "weather"],
        }).reset_index(drop=True)
        app.S.update(
            df=frame, all_dfs={"Sheet1": frame}, sheets=["Sheet1"],
            sheet="Sheet1", filename="demo.csv", cols=list(frame.columns),
            tc="Name", sc="Note", dc=list(frame.columns), flt={}, ft={},
            search="", sel=None, error=None,
        )
        self.client = TestClient(app.app)
        self.htmx = {"HX-Request": "true"}

    # ── P1-3: stale detail pane ────────────────────────────────────────
    def test_apply_oob_resets_detail_when_selection_filtered_out(self):
        app.S["sel"] = 1  # "Beta" — will be excluded by the search below
        response = self.client.post(
            "/apply", data={"search": "red"}, headers=self.htmx
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(app.S["sel"])
        # Response must carry an OOB #detail fragment showing the empty state
        self.assertIn('id="detail"', response.text)
        self.assertIn("Select a Row", response.text)

    def test_apply_oob_keeps_detail_when_selection_survives(self):
        app.S["sel"] = 0  # "Alpha" — note "red apple" matches the search
        response = self.client.post(
            "/apply", data={"search": "red"}, headers=self.htmx
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(app.S["sel"], 0)
        self.assertIn('id="detail"', response.text)

    # ── P1-6: sidebar filter groups rebuild on tc/sc change ────────────
    def test_cfg_returns_oob_col_filters(self):
        response = self.client.post(
            "/cfg", data={"tc": "Note"}, headers=self.htmx
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(app.S["tc"], "Note")
        self.assertIn('id="col-filters"', response.text)
        self.assertIn('hx-swap-oob="true"', response.text)

    # ── Upload / sheet / close round-trips ─────────────────────────────
    def test_upload_close_roundtrip(self):
        with open("test.csv", "rb") as f:
            response = self.client.post(
                "/upload", files={"file": ("test.csv", f, "text/csv")},
                headers=self.htmx,
            )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(app.S["df"])
        self.assertEqual(app.S["dc"], app.S["cols"])

        response = self.client.post("/close", headers=self.htmx)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(app.S["df"])
        self.assertEqual(app.S["cols"], [])
        self.assertIn('id="dropzone"', response.text)

    def test_sheet_switch_resets_viewer_state(self):
        with open("test_data.xlsx", "rb") as f:
            response = self.client.post(
                "/upload",
                files={"file": ("test_data.xlsx", f, "application/vnd.ms-excel")},
                headers=self.htmx,
            )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(app.S["sheets"]), 1)

        other = app.S["sheets"][1]
        app.S["search"] = "zzz"  # state that must be reset on switch
        response = self.client.post("/sheet", data={"s": other}, headers=self.htmx)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(app.S["sheet"], other)
        self.assertEqual(app.S["search"], "")
        self.assertEqual(app.S["flt"], {})
        self.assertIsNone(app.S["sel"])
        self.assertEqual(app.S["dc"], app.S["cols"])

    # ── /clear-error keeps a loaded file ───────────────────────────────
    def test_clear_error_keeps_loaded_file(self):
        app.S["error"] = "Unsupported file type. Upload .xlsx, .xls, or .csv."
        response = self.client.post("/clear-error", headers=self.htmx)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(app.S["error"])
        self.assertIsNotNone(app.S["df"])  # file survives
        self.assertIn("demo.csv", response.text)


if __name__ == "__main__":
    unittest.main()
