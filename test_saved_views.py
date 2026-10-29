"""Tests for saved views: explicit Save/Forget endpoints and automatic
restore of per-file/sheet view state (detail/filter columns, filters,
title/subtitle, search) on upload and sheet switch.

VIEWS_FILE is patched into a temp dir for the whole class — tests never
touch the real saved_views.json.
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd
from starlette.testclient import TestClient

import app


class SavedViewsTests(unittest.TestCase):
    def setUp(self):
        tmpdir = tempfile.mkdtemp(prefix="xv-views-")
        self.addCleanup(shutil.rmtree, tmpdir, True)
        patcher = mock.patch.object(
            app, "VIEWS_FILE", Path(tmpdir) / "views.json")
        patcher.start()
        self.addCleanup(patcher.stop)

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

    def seed(self, filename, sheet, view):
        views = app.load_views()
        views.setdefault(filename, {})[sheet] = view
        app.save_views(views)

    def upload(self, path, mime):
        with open(path, "rb") as f:
            return self.client.post(
                "/upload", files={"file": (Path(path).name, f, mime)},
                headers=self.htmx,
            )

    # ── /view/save ─────────────────────────────────────────────────────
    def test_save_writes_entry_and_section_shows_saved(self):
        app.S.update(flt={"Category": {"fruit"}}, ft={"Name": "al"},
                     search="red", dc=["Name", "Note"], fc=["Category"])
        response = self.client.post("/view/save", headers=self.htmx)
        self.assertEqual(response.status_code, 200)
        entry = json.loads(app.VIEWS_FILE.read_text(encoding="utf-8"))["demo.csv"]["Sheet1"]
        self.assertEqual(entry["tc"], "Name")
        self.assertEqual(entry["sc"], "Note")
        self.assertEqual(entry["dc"], ["Name", "Note"])
        self.assertEqual(entry["fc"], ["Category"])
        self.assertEqual(entry["flt"], {"Category": ["fruit"]})
        self.assertEqual(entry["ft"], {"Name": "al"})
        self.assertEqual(entry["search"], "red")
        self.assertIn("saved", response.text)
        self.assertIn("Forget", response.text)

    def test_save_without_file_is_noop(self):
        app.S["df"] = None
        response = self.client.post("/view/save", headers=self.htmx)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(app.VIEWS_FILE.exists())

    # ── restore on upload ──────────────────────────────────────────────
    def test_upload_applies_saved_view(self):
        self.seed("test.csv", "Sheet1", {
            "tc": "Role", "sc": "Status", "dc": ["Name", "Salary"],
            "fc": ["Department"], "flt": {"Department": ["Eng"]},
            "ft": {}, "search": "ali",
        })
        response = self.upload("test.csv", "text/csv")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(app.S["tc"], "Role")
        self.assertEqual(app.S["sc"], "Status")
        self.assertEqual(app.S["dc"], ["Name", "Salary"])
        self.assertEqual(app.S["fc"], ["Department"])
        self.assertEqual(app.S["flt"], {"Department": {"Eng"}})
        self.assertEqual(app.S["search"], "ali")
        self.assertTrue(app.S["view_restored"])
        self.assertIn("Saved view restored", response.text)

    def test_upload_without_saved_view_uses_defaults(self):
        response = self.upload("test.csv", "text/csv")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(app.S["tc"], "Name")
        self.assertEqual(app.S["dc"], app.S["cols"][:app.DC_DEFAULT])
        self.assertEqual(app.S["fc"], app.S["cols"][:app.FC_DEFAULT])
        self.assertEqual(app.S["flt"], {})
        self.assertEqual(app.S["search"], "")
        self.assertFalse(app.S["view_restored"])
        self.assertNotIn("Saved view restored", response.text)

    def test_restore_drops_unknown_columns(self):
        self.seed("test.csv", "Sheet1", {
            "tc": "Nope", "sc": "Gone", "dc": ["Name", "Ghost"],
            "fc": ["Department", "Phantom"],
            "flt": {"Phantom": ["x"], "Department": ["Eng"]},
            "ft": {}, "search": "",
        })
        self.upload("test.csv", "text/csv")
        self.assertEqual(app.S["tc"], "Name")   # bad tc → first column
        self.assertEqual(app.S["sc"], "")       # bad sc → cleared
        self.assertEqual(app.S["dc"], ["Name"])  # stale Ghost dropped
        self.assertEqual(app.S["fc"], ["Department"])
        self.assertEqual(app.S["flt"], {"Department": {"Eng"}})  # Phantom dropped

    # ── restore on sheet switch ────────────────────────────────────────
    def test_sheet_switch_applies_per_sheet_view(self):
        self.seed("test_data.xlsx", "Projects", {
            "tc": "Owner", "sc": "Project", "dc": ["Project", "Budget"],
            "fc": ["Owner", "Project"], "flt": {}, "ft": {"Project": "q"}, "search": "x",
        })
        self.upload("test_data.xlsx", "application/vnd.ms-excel")
        # Employees has no view → upload stays on defaults
        self.assertEqual(app.S["sheet"], "Employees")
        self.assertFalse(app.S["view_restored"])
        self.assertEqual(app.S["dc"], app.S["cols"][:app.DC_DEFAULT])

        self.client.post("/sheet", data={"s": "Projects"}, headers=self.htmx)
        self.assertEqual(app.S["sheet"], "Projects")
        self.assertTrue(app.S["view_restored"])
        self.assertEqual(app.S["tc"], "Owner")
        self.assertEqual(app.S["dc"], ["Project", "Budget"])
        self.assertEqual(app.S["fc"], ["Owner", "Project"])
        self.assertEqual(app.S["ft"], {"Project": "q"})
        self.assertEqual(app.S["search"], "x")

        # Switch back to a sheet without a view → defaults again
        self.client.post("/sheet", data={"s": "Employees"}, headers=self.htmx)
        self.assertFalse(app.S["view_restored"])
        self.assertEqual(app.S["dc"], app.S["cols"][:app.DC_DEFAULT])
        self.assertEqual(app.S["flt"], {})

    # ── /view/forget ───────────────────────────────────────────────────
    def test_forget_removes_entry(self):
        self.client.post("/view/save", headers=self.htmx)
        self.assertIn("demo.csv",
                      json.loads(app.VIEWS_FILE.read_text(encoding="utf-8")))
        response = self.client.post("/view/forget", headers=self.htmx)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("demo.csv",
                         json.loads(app.VIEWS_FILE.read_text(encoding="utf-8")))
        self.assertIn("Save view", response.text)

    def test_forget_missing_entry_is_noop(self):
        response = self.client.post("/view/forget", headers=self.htmx)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Save view", response.text)


if __name__ == "__main__":
    unittest.main()
