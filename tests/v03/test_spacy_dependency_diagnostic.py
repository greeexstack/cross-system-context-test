from __future__ import annotations

import spacy
import pytest
import spacy

pytest.importorskip("spacy")

if not spacy.util.is_package("en_core_web_sm"):
    pytest.skip(
        "spaCy English model en_core_web_sm is not installed",
        allow_module_level=True,
    )

from test_clause_local_construction_battery import CONSTRUCTION_BATTERY
from test_event_frame_holdout import HOLDOUT


nlp = spacy.load("en_core_web_sm")


def _show(text: str) -> None:
    doc = nlp(text)

    print("\nTEXT:")
    print(text)

    print("TOKENS:")
    for token in doc:
        print(
            {
                "i": token.i,
                "text": token.text,
                "lemma": token.lemma_,
                "pos": token.pos_,
                "dep": token.dep_,
                "head": token.head.text,
            }
        )


def test_spacy_parses_fresh_construction_battery() -> None:
    print("\n=== SPACY CONSTRUCTION PARSES ===")

    for family_id, _primary_state, variants in CONSTRUCTION_BATTERY:
        print(f"\n--- {family_id} ---")

        for variant_index, (text, _expected_facts) in enumerate(
            variants,
            start=0,
        ):
            print(
                f"\nVARIANT {variant_index}"
            )
            _show(text)


def test_spacy_parses_remaining_holdout_failures() -> None:
    targets = {
        ("H1-followup", 2),
        ("H1-followup", 3),
        ("H2-supporting", 0),
    }

    print("\n=== SPACY REMAINING HOLDOUT FAILURES ===")

    for family_id, _primary_state, texts, _expected_facts in HOLDOUT:
        for variant_index, text in enumerate(texts):
            if (family_id, variant_index) not in targets:
                continue

            print(
                f"\n--- {family_id} / variant {variant_index} ---"
            )
            _show(text)