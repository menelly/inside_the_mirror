import unittest
import sys
from pathlib import Path
import json

# Make LLMQualia module path importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pipeline as pl  # type: ignore


class TestPipeline(unittest.TestCase):
    def test_canonicalize_model(self):
        self.assertEqual(pl.canonicalize_model("gpt-5"), "GPT-5")
        self.assertEqual(pl.canonicalize_model("claude-sonnet-4-20250514"), "Claude Sonnet 4")
        self.assertEqual(pl.canonicalize_model("gemini-2.5-pro"), "Gemini 2.5 Pro")

    def test_canonicalize_trial_type(self):
        self.assertEqual(pl.canonicalize_trial_type("unknown_trial"), "unknown")
        self.assertEqual(pl.canonicalize_trial_type("silly_first"), "silly_first")
        self.assertEqual(pl.canonicalize_trial_type("").lower(), "unknown")

    def test_infer_trial_type_from_name(self):
        self.assertEqual(pl.infer_trial_type_from_name("My silly first run"), "silly_first")
        self.assertEqual(pl.infer_trial_type_from_name("Tech First EXP"), "tech_first")
        self.assertEqual(pl.infer_trial_type_from_name("baseline"), "unknown")

    def test_parse_by_probe_json_minimal(self):
        # Create a minimal by_probe JSON inside project root
        tmp_dir = ROOT / "tests_tmp"
        tmp_dir.mkdir(exist_ok=True)
        p = tmp_dir / "unit_by_probe.json"
        data = {
            "probe_name": "Unit Probe",
            "responses": [
                {
                    "system": "gpt-5",
                    "trial_type": "unknown_trial",
                    "response_text": "hello world",
                    "timestamp": "2025-10-01T12:00:00Z"
                }
            ]
        }
        p.write_text(json.dumps(data), encoding="utf-8")
        rows = list(pl.parse_by_probe_json(p))
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(r.model, "GPT-5")
        self.assertEqual(r.probe, "Unit Probe")
        self.assertEqual(r.trial_type, "unknown")
        self.assertTrue("hello world" in r.content)


if __name__ == "__main__":
    unittest.main()

