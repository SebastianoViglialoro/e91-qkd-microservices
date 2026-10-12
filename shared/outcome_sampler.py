"""Centralized statistical measurement; not physically local or device independent.

The singlet law and noise/Eve transformations are moved unchanged from sifting.
"""
import math
import random

OUTCOMES = (-1, 1)

def sample_singlet_outcomes(alice_angle_degrees: float, bob_angle_degrees: float) -> tuple[int, int]:
    alice_angle = math.radians(alice_angle_degrees)
    bob_angle = math.radians(bob_angle_degrees)
    expectation = -math.cos(alice_angle - bob_angle)
    same_probability = max(0.0, min(1.0, (1.0 + expectation) / 2.0))

    alice_outcome = random.choice(OUTCOMES)
    same_outcome = random.random() < same_probability
    bob_outcome = alice_outcome if same_outcome else -alice_outcome
    return alice_outcome, bob_outcome


def correlate_with_singlet_sampler(items: list[dict]) -> list[dict]:
    correlated = []
    for item in items:
        alice_outcome, bob_outcome = sample_singlet_outcomes(
            item["alice_basis_angle"],
            item["bob_basis_angle"],
        )
        noise_type = item.get("noise_type", "bit_flip")
        attack_type = item.get("attack_type", "randomize")

        # Symbolic controlled-noise strategies:
        # - bit_flip: Bob's sampled outcome is inverted.
        # - depolarizing: Bob's sampled outcome is randomized, approximating
        #   loss of directional information without modelling a full channel.
        if item.get("noise_applied", False):
            if noise_type == "depolarizing":
                bob_outcome = random.choice(OUTCOMES)
            else:
                bob_outcome = -bob_outcome

        # Symbolic Eve strategies:
        # - randomize: Bob's outcome is randomized on attacked rounds.
        # - intercept_resend: simplified intercept/resend model; Eve breaks
        #   the entangled correlation, implemented here as an independent Bob
        #   outcome while preserving a separate attack_type in the results.
        if item.get("eve_applied", False):
            bob_outcome = random.choice(OUTCOMES)
        correlated.append(
            {
                **item,
                "alice_outcome": alice_outcome,
                "bob_outcome": bob_outcome,
                "correlation_model": "classical_singlet_sampler",
                "noise_type": noise_type,
                "attack_type": attack_type,
            }
        )
    return correlated


def sample_receiver_records(alice_records: list[dict], bob_records: list[dict]) -> tuple[list[dict], list[dict]]:
    """Join selected bases, sample once per delivered pair, retain receiver metadata."""
    alice_ids = [record["pair_id"] for record in alice_records]
    bob_by_pair = {record["pair_id"]: record for record in bob_records}
    if (len(set(alice_ids)) != len(alice_ids)
            or len(bob_by_pair) != len(bob_records)
            or set(alice_ids) != set(bob_by_pair)):
        raise ValueError("Receiver selections must contain the same unique delivered pairs")
    alice_measured, bob_measured = [], []
    for alice in alice_records:
        bob = bob_by_pair[alice["pair_id"]]
        pair = {
            "alice_basis_angle": alice["basis_angle"],
            "bob_basis_angle": bob["basis_angle"],
            "noise_applied": alice.get("noise_applied", False) or bob.get("noise_applied", False),
            "noise_type": bob.get("noise_type", alice.get("noise_type", "bit_flip")),
            "eve_applied": alice.get("eve_applied", False) or bob.get("eve_applied", False),
            "attack_type": bob.get("attack_type", alice.get("attack_type", "randomize")),
        }
        measured = correlate_with_singlet_sampler([pair])[0]
        alice_measured.append({**alice, "outcome": measured["alice_outcome"]})
        bob_measured.append({**bob, "outcome": measured["bob_outcome"]})
    return alice_measured, bob_measured
