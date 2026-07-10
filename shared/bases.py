from __future__ import annotations

from dataclasses import dataclass


BASIS_MODEL = "TWO_KEY_BASES_ONE_CHECK_BASIS"


@dataclass(frozen=True)
class MeasurementBasis:
    name: str
    angle_degrees: float
    role: str


# Corrected E91 baseline:
# - K0/K0 and K1/K1 are reserved for key generation.
# - CHSH uses four explicit non-key/control combinations involving the check basis C.
# - Angles are intentionally centralized here so the basis model can evolve without
#   changing Alice, Bob, Classical Channel, or Sifting service contracts.
ALICE_BASES = (
    MeasurementBasis(name="C", angle_degrees=0.0, role="check"),
    MeasurementBasis(name="K0", angle_degrees=45.0, role="key"),
    MeasurementBasis(name="K1", angle_degrees=90.0, role="key"),
)

BOB_BASES = (
    MeasurementBasis(name="K0", angle_degrees=45.0, role="key"),
    MeasurementBasis(name="K1", angle_degrees=90.0, role="key"),
    MeasurementBasis(name="C", angle_degrees=-45.0, role="check"),
)

ALICE_BASIS_NAMES = tuple(basis.name for basis in ALICE_BASES)
BOB_BASIS_NAMES = tuple(basis.name for basis in BOB_BASES)

ALICE_BASIS_BY_NAME = {basis.name: basis for basis in ALICE_BASES}
BOB_BASIS_BY_NAME = {basis.name: basis for basis in BOB_BASES}

CHSH_TERMS = (
    {"alice": "C", "bob": "K0", "coefficient": 1},
    {"alice": "C", "bob": "C", "coefficient": 1},
    {"alice": "K1", "bob": "K0", "coefficient": 1},
    {"alice": "K1", "bob": "C", "coefficient": -1},
)


def alice_basis_names() -> list[str]:
    return list(ALICE_BASIS_NAMES)


def bob_basis_names() -> list[str]:
    return list(BOB_BASIS_NAMES)


def get_chsh_terms() -> list[dict]:
    return [dict(term) for term in CHSH_TERMS]


def _alice_role(alice_basis: str) -> str | None:
    basis = ALICE_BASIS_BY_NAME.get(alice_basis)
    return basis.role if basis else None


def _bob_role(bob_basis: str) -> str | None:
    basis = BOB_BASIS_BY_NAME.get(bob_basis)
    return basis.role if basis else None


def is_key_pair(alice_basis: str, bob_basis: str) -> bool:
    return (
        alice_basis == bob_basis
        and _alice_role(alice_basis) == "key"
        and _bob_role(bob_basis) == "key"
    )


def is_key_match(alice_basis: str, bob_basis: str) -> bool:
    return is_key_pair(alice_basis, bob_basis)


def is_bell_pair(alice_basis: str, bob_basis: str) -> bool:
    return any(
        term["alice"] == alice_basis and term["bob"] == bob_basis
        for term in CHSH_TERMS
    )


def is_check_basis(alice_basis: str, bob_basis: str) -> bool:
    return _alice_role(alice_basis) == "check" or _bob_role(bob_basis) == "check"


def classify_basis_pair(alice_basis: str, bob_basis: str) -> str:
    if is_key_pair(alice_basis, bob_basis):
        return "key"
    if is_bell_pair(alice_basis, bob_basis):
        return "bell"
    return "discarded"


KEY_BASIS_PAIRS = frozenset(
    (alice_basis.name, bob_basis.name)
    for alice_basis in ALICE_BASES
    for bob_basis in BOB_BASES
    if is_key_pair(alice_basis.name, bob_basis.name)
)

BELL_BASIS_PAIRS = frozenset((term["alice"], term["bob"]) for term in CHSH_TERMS)
CHSH_BASIS_PAIRS = BELL_BASIS_PAIRS
