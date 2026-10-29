"""Tests for the local-tool hardening (security audit follow-up).

Covers:
- DNS-rebinding defense: dotted non-loopback Host headers are rejected
- CSRF defense: POSTs with a foreign Origin are rejected; same-origin and
  Origin-less (curl/test) POSTs pass
- Security headers ship on every response
"""

import unittest

import pandas as pd
from starlette.testclient import TestClient

import app


def demo_client(base_url="http://testserver"):
    frame = pd.DataFrame({"A": ["1"], "B": ["2"]}).reset_index(drop=True)
    app.S.update(
        df=frame, all_dfs={"S": frame}, sheets=["S"], sheet="S",
        filename="demo.csv", cols=list(frame.columns), tc="A", sc="B",
        dc=list(frame.columns), fc=list(frame.columns),
        flt={}, ft={}, search="", sel=None, error=None,
    )
    return TestClient(app.app, base_url=base_url)


class HostGuardTests(unittest.TestCase):
    def test_loopback_host_allowed(self):
        self.assertEqual(demo_client("http://127.0.0.1:8765").get("/").status_code, 200)

    def test_localhost_host_allowed(self):
        self.assertEqual(demo_client("http://localhost:8765").get("/").status_code, 200)

    def test_dotted_external_host_rejected(self):
        # DNS-rebinding candidate: evil.tld resolving to 127.0.0.1
        self.assertEqual(demo_client("http://evil.example:8765").get("/").status_code, 403)

    def test_testclient_default_host_allowed(self):
        self.assertEqual(demo_client().get("/").status_code, 200)


class CsrfGuardTests(unittest.TestCase):
    def test_post_without_origin_allowed(self):
        # curl / scripted use: no Origin header at all
        self.assertEqual(demo_client().post("/close").status_code, 200)

    def test_post_same_origin_allowed(self):
        c = demo_client()
        r = c.post("/close", headers={"Origin": "http://testserver"})
        self.assertEqual(r.status_code, 200)

    def test_post_foreign_origin_rejected(self):
        c = demo_client()
        r = c.post("/close", headers={"Origin": "https://evil.example"})
        self.assertEqual(r.status_code, 403)
        self.assertIsNotNone(app.S["df"])  # state unchanged

    def test_get_with_foreign_origin_still_served(self):
        # Guard only covers state-changing methods; GET is protected by Host.
        c = demo_client()
        r = c.get("/", headers={"Origin": "https://evil.example"})
        self.assertEqual(r.status_code, 200)


class SecurityHeadersTests(unittest.TestCase):
    def test_headers_present(self):
        r = demo_client().get("/")
        csp = r.headers.get("content-security-policy", "")
        self.assertIn("default-src 'self'", csp)
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertIn("connect-src 'self'", csp)
        self.assertEqual(r.headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(r.headers.get("x-frame-options"), "DENY")
        self.assertEqual(r.headers.get("referrer-policy"), "same-origin")


if __name__ == "__main__":
    unittest.main()
