import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("lab", ROOT / "scripts/lab.py")
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.base = json.loads((ROOT / "config/base.json").read_text())
        self.cfg = lab.build_config(self.base)

    def test_rejects_live_mode(self):
        for value in (False, "false", 1, None):
            with self.subTest(value=value):
                self.cfg["dry_run"] = value
                with self.assertRaises(ValueError):
                    lab.validate(self.cfg)

    def test_rejects_exchange_credentials(self):
        for key in ("key", "secret", "password", "uid", "apiKey"):
            cfg = copy.deepcopy(self.cfg)
            cfg["exchange"][key] = "credential"
            with self.assertRaises(ValueError):
                lab.validate(cfg)

    def test_rejects_force_entry(self):
        self.cfg["force_entry_enable"] = True
        with self.assertRaises(ValueError):
            lab.validate(self.cfg)

    def test_rejects_futures(self):
        self.cfg["trading_mode"] = "futures"
        with self.assertRaises(ValueError):
            lab.validate(self.cfg)

    def test_independent_secrets_and_no_template_mutation(self):
        other = lab.build_config(self.base)
        for key in ("password", "jwt_secret_key", "ws_token"):
            self.assertNotEqual(self.cfg["api_server"][key], other["api_server"][key])
            self.assertNotIn(key, self.base["api_server"])

    def test_json_roundtrip_special_characters(self):
        self.cfg["api_server"]["password"] = "a'\"\\$" * 10
        restored = json.loads(json.dumps(self.cfg))
        lab.validate(restored)
        self.assertEqual(restored, self.cfg)

    def test_smoke_success_without_leaking_secrets(self):
        replies = [(200, {"status": "pong"}), (401, {}), (401, {}),
                   (200, {"access_token": "TEST_BEARER_SECRET"}),
                   (200, {"dry_run": True, "strategy": "ObserveStrategy"}), (200, [])]
        out = io.StringIO()
        with patch.object(lab, "local_config", return_value=self.cfg), \
             patch.object(lab, "request", side_effect=replies) as request, \
             contextlib.redirect_stdout(out):
            lab.smoke()
        self.assertIn("PASS", out.getvalue())
        self.assertNotIn("TEST_BEARER_SECRET", out.getvalue())
        self.assertNotIn(self.cfg["api_server"]["password"], out.getvalue())
        self.assertTrue(request.call_args_list[3].args[1].startswith("Basic "))
        self.assertEqual(request.call_args_list[4].args[1], "Bearer TEST_BEARER_SECRET")

    def test_smoke_rejects_anonymous_access(self):
        with patch.object(lab, "local_config", return_value=self.cfg), \
             patch.object(lab, "request", side_effect=[(200, {"status": "pong"}), (200, {})]):
            with self.assertRaisesRegex(ValueError, "sem autenticação"):
                lab.smoke()

    def test_smoke_rejects_effective_live_mode(self):
        replies = [(200, {"status": "pong"}), (401, {}), (401, {}),
                   (200, {"access_token": "test"}), (200, {"dry_run": False})]
        with patch.object(lab, "local_config", return_value=self.cfg), \
             patch.object(lab, "request", side_effect=replies):
            with self.assertRaisesRegex(ValueError, "dry_run"):
                lab.smoke()

    def test_compose_rejects_exposed_api(self):
        model = {"services": {"freqtrade": {"ports": [{"host_ip": "0.0.0.0", "published": "8080"}]}}}
        with patch.object(lab, "run", return_value=json.dumps(model)):
            with self.assertRaisesRegex(ValueError, "127.0.0.1"):
                lab.assert_compose()

    def test_compose_accepts_local_pinned_dry_run(self):
        service = {"ports": [{"host_ip": "127.0.0.1", "published": "8080"}],
                   "environment": {"FREQTRADE__DRY_RUN": "true"},
                   "image": "freqtradeorg/freqtrade@sha256:" + "a" * 64}
        with patch.object(lab, "run", return_value=json.dumps({"services": {"freqtrade": service}})):
            lab.assert_compose()

    def test_redirects_are_not_followed(self):
        self.assertIsNone(lab.NoRedirect().redirect_request(None, None, 302, "", {}, "http://example.invalid"))


if __name__ == "__main__":
    unittest.main()
