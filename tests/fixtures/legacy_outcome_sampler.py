"""Frozen pre-refactor sampler, retained only as an independent regression oracle."""
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


