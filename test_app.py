import unittest

import pandas as pd
from fasthtml.common import to_xml
from starlette.testclient import TestClient

import app


class ViewerBehaviorTests(unittest.TestCase):
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
            search="", sel=None, error="",
        )
        self.client = TestClient(app.app)
        self.htmx = {"HX-Request": "true"}

    def test_global_search_matches_any_column(self):
        app.S["search"] = "red"
        self.assertEqual(list(app.filt().index), [0, 2])

    def test_filtered_cards_keep_original_row_identity(self):
        app.S["search"] = "red"
        cards = to_xml(app.row_list(app.filt()))
        self.assertIn('hx-get="/row/0"', cards)
        self.assertIn('hx-get="/row/2"', cards)
        response = self.client.get("/row/2", headers=self.htmx)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Gamma", response.text)

    def test_detail_columns_can_be_intentionally_empty(self):
        app.S["sel"] = 1
        response = self.client.post(
            "/cfg/detail-cols", data={"dc_present": "1"}, headers=self.htmx
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(app.S["dc"], [])
        self.assertIn("No detail columns selected.", response.text)

    def test_detail_columns_show_only_selected_values(self):
        app.S["sel"] = 2
        response = self.client.post(
            "/cfg/detail-cols",
            data={"dc_present": "1", "dc": "Note"},
            headers=self.htmx,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(app.S["dc"], ["Note"])
        self.assertIn('data-copy-value="red sky"', response.text)
        self.assertNotIn('data-copy-value="Gamma"', response.text)

    def test_partial_filter_submission_preserves_other_filters(self):
        app.S["flt"] = {"Category": {"fruit"}}
        app.S["ft"] = {"Note": "apple"}
        response = self.client.post(
            "/apply", data={"search": "Alpha"}, headers=self.htmx
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(app.S["flt"], {"Category": {"fruit"}})
        self.assertEqual(app.S["ft"], {"Note": "apple"})
        self.assertIn('hx-swap-oob="true"', response.text)

    def test_subtitle_column_can_be_cleared(self):
        response = self.client.post("/cfg", data={"sc": ""}, headers=self.htmx)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(app.S["sc"], "")
        self.assertIn('id="main-wrap"', response.text)


if __name__ == "__main__":
    unittest.main()
