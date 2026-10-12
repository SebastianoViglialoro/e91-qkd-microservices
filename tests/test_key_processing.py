"""Regression checks for centralized, demonstrative key derivation.

Run from the repository root:
    .venv/bin/python -m unittest discover -s tests -v
"""
import csv
import hashlib
import importlib.util
from collections import Counter
from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_service(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


key_processing = load_service("tested_key_processing", "key-processing/app/main.py")
# Sifting imports its optional circuit sampler via its service-local app package.
with patch.object(sys, "path", [str(ROOT / "sifting-bell-test"), str(ROOT), *sys.path]):
    sifting = load_service("tested_sifting", "sifting-bell-test/app/main.py")


def make_request(raw_bits, error_positions=(), status="secure", minimum=256):
    errors = set(error_positions)
    subset, records = [], []
    for index, bit in enumerate(raw_bits):
        alice = int(bit)
        bob_corrected = 1 - alice if index in errors else alice
        basis = "K0" if index % 2 == 0 else "K1"
        angle = 45.0 if basis == "K0" else 90.0
        subset.append({
            "pair_id": str(index),
            "alice_basis": basis,
            "bob_basis": basis,
            "alice_basis_angle": angle,
            "bob_basis_angle": angle,
            "alice_outcome": 1 if alice else -1,
            "bob_outcome": 1 if 1 - bob_corrected else -1,
        })
        records.append({
            "pair_id": str(index),
            "alice_bit": alice,
            "bob_corrected_bit": bob_corrected,
            "error": index in errors,
        })
    return key_processing.GenerateKeyRequest(
        session_id="key-processing-test",
        reconciled={"key_subset": subset},
        evaluation={"security_status": status, "key_records": records},
        min_sifted_key_length=minimum,
    )


class KeyProcessingTests(unittest.TestCase):
    def setUp(self):
        self.log_patch = patch.object(key_processing.logger, "info")
        self.log_patch.start()
        self.addCleanup(self.log_patch.stop)

    def assert_hash_input(self, request, expected_bits):
        before = deepcopy(request.model_dump())
        real_sha256 = hashlib.sha256
        with patch.object(key_processing.hashlib, "sha256", wraps=real_sha256) as digest:
            result = key_processing.generate_key(request)
            digest.assert_called_once_with(expected_bits.encode("utf-8"))
        self.assertEqual(result["final_key"], real_sha256(expected_bits.encode()).hexdigest())
        self.assertEqual(result["sifted_key_length"], len(expected_bits))
        self.assertEqual(result["raw_key_length"], len(request.reconciled["key_subset"]))
        self.assertEqual(result["key_status"], "generated")
        self.assertEqual(result["final_key_length"], 256)
        self.assertEqual(result["privacy_amplification"], "simplified_hash_demo")
        self.assertEqual(request.model_dump(), before)
        return result

    def test_zero_qber_hashes_unchanged_raw_sequence(self):
        raw = "01101001" * 40
        self.assert_hash_input(make_request(raw), raw)

    def test_discordant_positions_are_excluded_in_original_order(self):
        raw = "01101001" * 40
        errors = {0, 3, 19, 100, 319}
        clean = "".join(bit for i, bit in enumerate(raw) if i not in errors)
        request = make_request(raw, errors)
        # Match by pair_id, not by the ordering of evaluation records.
        request.evaluation["key_records"].reverse()
        result = self.assert_hash_input(request, clean)
        self.assertLess(len(clean), len(raw))
        self.assertNotEqual(result["final_key"], hashlib.sha256(raw.encode()).hexdigest())
        self.assertEqual(result["raw_key_preview"], raw[:32])

    def test_fallback_outcomes_apply_bob_inversion_before_filtering(self):
        raw = "10110010" * 40
        errors = {1, 11, 31, 111}
        request = make_request(raw, errors)
        request.evaluation.pop("key_records")
        clean = "".join(bit for i, bit in enumerate(raw) if i not in errors)
        self.assert_hash_input(request, clean)

    def test_minimum_is_applied_to_clean_material_including_equality(self):
        raw = "01" * 150
        self.assert_hash_input(make_request(raw, range(44)), raw[44:])
        with patch.object(key_processing.hashlib, "sha256") as digest:
            result = key_processing.generate_key(make_request(raw, range(45)))
            digest.assert_not_called()
        self.assertEqual(result["raw_key_length"], 300)
        self.assertEqual(result["sifted_key_length"], 255)
        self.assertEqual(result["key_status"], "insufficient_key_material")
        self.assertIsNone(result["final_key"])
        self.assertEqual(result["final_key_length"], 0)

    def test_rejected_security_states_never_hash(self):
        for status, expected in [("degraded", "discarded_degraded"), ("insecure", "discarded")]:
            for raw in ["01" * 160, "01"]:
                with self.subTest(status=status, raw_length=len(raw)):
                    with patch.object(key_processing.hashlib, "sha256") as digest:
                        result = key_processing.generate_key(make_request(raw, status=status))
                        digest.assert_not_called()
                    self.assertEqual(result["key_status"], expected)
                    self.assertIsNone(result["final_key"])
                    self.assertEqual(result["final_key_length"], 0)

    def test_qber_denominator_remains_all_key_rounds(self):
        request = make_request("01" * 150, range(15))
        subset = request.reconciled["key_subset"]
        for item in subset[:15]:
            item.update(noise_applied=True, noise_type="bit_flip", noise_level=0.05)
        # Outcomes already include the flips; sifting must not apply them again.
        evaluation = sifting.evaluate(sifting.EvaluateRequest(
            session_id=request.session_id, reconciled=request.reconciled,
        ))
        request.evaluation = evaluation
        result = key_processing.generate_key(request)
        self.assertEqual(evaluation["error_count"], 15)
        self.assertEqual(evaluation["compared_bits"], 300)
        self.assertEqual(result["raw_key_length"], 300)
        self.assertEqual(result["sifted_key_length"], 285)
        self.assertEqual(evaluation["qber"], 15 / result["raw_key_length"])
        # No Bell samples: preserve the existing degraded classification.
        self.assertEqual(result["key_status"], "discarded_degraded")

    def test_saved_campaign_decisions_preserved_for_all_360_rows(self):
        """Replay saved lengths/statuses with synthetic bits, not a new campaign.

        The CSV does not contain original bit strings. Reconstruct only the
        quantities needed to verify the key-processing decision for every row.
        """
        path = ROOT / "results/final/final_experiment_runs.csv"
        with path.open(newline="", encoding="utf-8") as source:
            rows = list(csv.DictReader(source))
        self.assertEqual(len(rows), 360)
        security_counts, key_counts = Counter(), Counter()
        for row in rows:
            with self.subTest(scenario=row["scenario_name"], repeat=row["repeat_id"]):
                raw_length = int(row["raw_key_length"])
                clean_length = int(row["sifted_key_length"])
                errors = raw_length - clean_length
                raw = ("01" * ((raw_length + 1) // 2))[:raw_length]
                request = make_request(
                    raw, range(errors), row["security_status"], int(row["min_sifted_key_length"]),
                )
                result = key_processing.generate_key(request)
                self.assertEqual(result["key_status"], row["key_status"])
                self.assertEqual(result["key_reason"], row["key_reason"])
                self.assertEqual(result["raw_key_length"], raw_length)
                self.assertEqual(result["sifted_key_length"], clean_length)
                self.assertEqual(result["final_key_length"], int(row["final_key_length"]))
                self.assertAlmostEqual(float(row["qber"]), errors / raw_length, delta=0.000050001)
                if result["key_status"] == "generated":
                    self.assertEqual(result["final_key"], hashlib.sha256(raw[errors:].encode()).hexdigest())
                else:
                    self.assertIsNone(result["final_key"])
                security_counts[row["security_status"]] += 1
                key_counts[result["key_status"]] += 1
        self.assertEqual(security_counts, {"secure": 228, "degraded": 91, "insecure": 41})
        self.assertEqual(key_counts, {
            "generated": 218, "discarded_degraded": 91,
            "discarded": 41, "insufficient_key_material": 10,
        })


if __name__ == "__main__":
    unittest.main()
