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
            tc="Name", sc="Note", dc=list(frame.columns), fc=list(frame.columns),
            flt={}, ft={}, search="", sel=None, error=None,
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

    # ── Lazy sidebar: stubs only, groups fetched on expand ─────────────
    def test_sidebar_renders_lazy_stubs_only(self):
        from fasthtml.common import to_xml
        cf = to_xml(app.col_filters())
        self.assertIn('hx-get="/filter/2"', cf)
        self.assertIn('id="fgb-2"', cf)
        self.assertIn('hx-trigger="toggle once"', cf)
        # No eager filter controls — that was the 431-column killer
        self.assertNotIn('type="checkbox"', cf)
        self.assertNotIn('name="ft_', cf)

    def test_sidebar_has_picker_search_and_cap_footer(self):
        from fasthtml.common import to_xml
        html = to_xml(app.layout())
        # Column search lives in the Filter Columns picker, above the
        # #col-filters group list; the cap footer ships inside it.
        self.assertIn('id="fc-search"', html)
        self.assertIn('id="filter-pick"', html)
        self.assertLess(html.index('id="fc-search"'), html.index('id="col-filters"'))
        cf = to_xml(app.col_filters())
        self.assertIn('id="colf-more"', cf)

    # ── Filter Columns picker (like Detail Columns) ────────────────────
    def test_upload_defaults_to_first_fc_columns(self):
        orig = app.FC_DEFAULT
        app.FC_DEFAULT = 2
        try:
            with open("test.csv", "rb") as f:
                self.client.post(
                    "/upload", files={"file": ("test.csv", f, "text/csv")},
                    headers=self.htmx,
                )
        finally:
            app.FC_DEFAULT = orig
        self.assertEqual(app.S["fc"], app.S["cols"][:2])

    def test_col_filters_renders_only_selected_columns(self):
        from fasthtml.common import to_xml
        app.S["fc"] = ["Category"]
        cf = to_xml(app.col_filters())
        self.assertIn('hx-get="/filter/2"', cf)  # Category
        self.assertNotIn('hx-get="/filter/0"', cf)  # Name not selected
        self.assertNotIn('hx-get="/filter/1"', cf)  # Note not selected

    def test_cfg_filter_cols_updates_fc_and_drops_removed_filters(self):
        app.S["flt"] = {"Note": {"red"}, "Category": {"fruit"}}
        app.S["ft"] = {"Name": "alpha"}
        response = self.client.post(
            "/cfg/filter-cols",
            data={"fc_present": "1", "fc": ["Category"]},
            headers=self.htmx,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(app.S["fc"], ["Category"])
        self.assertNotIn("Note", app.S["flt"])  # deselected → filter removed
        self.assertNotIn("Name", app.S["ft"])
        self.assertEqual(app.S["flt"]["Category"], {"fruit"})  # kept
        self.assertIn('id="col-filters"', response.text)

    def test_sidebar_stub_badges_active_filters_without_pandas(self):
        app.S["flt"] = {"Category": {"fruit", "color"}}
        from fasthtml.common import to_xml
        cf = to_xml(app.col_filters())
        self.assertIn("2 selected", cf)

    def test_filter_endpoint_chip_form_for_low_cardinality(self):
        response = self.client.get("/filter/2", headers=self.htmx)  # Category
        self.assertEqual(response.status_code, 200)
        self.assertIn('name="f_Category"', response.text)
        self.assertIn('name="f_Category_present"', response.text)
        self.assertIn('type="checkbox"', response.text)

    def test_filter_endpoint_text_input_for_high_cardinality(self):
        orig = app.TH
        app.TH = 0  # force every column into the text-filter branch
        try:
            response = self.client.get("/filter/0", headers=self.htmx)
        finally:
            app.TH = orig
        self.assertIn('name="ft_Name"', response.text)
        self.assertNotIn('type="checkbox"', response.text)

    def test_filter_endpoint_rejects_out_of_range_index(self):
        response = self.client.get("/filter/999", headers=self.htmx)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('type="checkbox"', response.text)

    # ── Detail-column default cap ───────────────────────────────────────
    def test_upload_caps_default_detail_columns(self):
        orig = app.DC_DEFAULT
        app.DC_DEFAULT = 2
        try:
            with open("test.csv", "rb") as f:
                self.client.post(
                    "/upload", files={"file": ("test.csv", f, "text/csv")},
                    headers=self.htmx,
                )
        finally:
            app.DC_DEFAULT = orig
        self.assertEqual(len(app.S["cols"]), 5)
        self.assertEqual(app.S["dc"], app.S["cols"][:2])

    def test_oversized_upload_sets_error_and_keeps_loaded_file(self):
        orig = app.MAX_FILE_SIZE
        app.MAX_FILE_SIZE = 10  # smaller than test.csv
        try:
            with open("test.csv", "rb") as f:
                response = self.client.post(
                    "/upload", files={"file": ("test.csv", f, "text/csv")},
                    headers=self.htmx,
                )
        finally:
            app.MAX_FILE_SIZE = orig
        self.assertEqual(response.status_code, 200)
        self.assertIn("File too large", response.text)
        self.assertIsNotNone(app.S["df"])  # previous file untouched
        self.assertEqual(app.S["filename"], "demo.csv")

    # ── /clear-error keeps a loaded file ───────────────────────────────
    def test_clear_error_keeps_loaded_file(self):
        app.S["error"] = "Unsupported file type. Upload .xlsx, .xls, or .csv."
        response = self.client.post("/clear-error", headers=self.htmx)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(app.S["error"])
        self.assertIsNotNone(app.S["df"])  # file survives
        self.assertIn("demo.csv", response.text)


    # ── Theme settings popover + Frost/Midnight themes ────────────────
    def test_layout_has_settings_button_and_theme_options(self):
        from fasthtml.common import to_xml
        html = to_xml(app.layout())
        self.assertIn('id="settings-btn"', html)
        self.assertIn('id="theme-pop"', html)
        for key in ("dark", "light", "frost", "midnight"):
            self.assertIn(f'data-theme-opt="{key}"', html)
        self.assertNotIn('id="theme-toggle"', html)
        # Gear icon must be a real SVG path — fasthtml.common.Path is
        # pathlib.Path and silently renders "." instead.
        self.assertIn('<path d="M19.4', html)

    def test_frost_midnight_theme_blocks(self):
        self.assertIn('[data-theme="frost"]', app.CSS)
        self.assertIn('[data-theme="midnight"]', app.CSS)

    def test_head_js_defaults_to_frost(self):
        self.assertIn("'frost'", app.HEAD_JS)
        self.assertIn("ok.indexOf(t)<0", app.HEAD_JS)


if __name__ == "__main__":
    unittest.main()
