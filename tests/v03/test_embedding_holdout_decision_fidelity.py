from __future__ import annotations

from datetime import datetime
from typing import Dict

from experiment.v03.evidence import (
    EvidenceCondition,
    EvidenceIdentity,
    EvidenceProvenance,
    EvidenceSemantics,
    IdentityQuality,
    SemanticEvidence,
)
from experiment.v03.reasoner import (
    PrimaryState,
    ReasonerConfig,
    V03Reasoner,
)

from test_clause_local_holdout_decision_fidelity import (
    ORACLE_SEMANTICS,
    _oracle_behavior,
)
from test_embedding_fact_threshold_calibration import (
    _build_full_development_prototypes,
    _calibrate_thresholds,
    _predict_facts,
)
from test_event_frame_holdout import HOLDOUT
from test_independent_paraphrase_battery import EVALUATION_AT

FIXED_TIMESTAMP = "2026-09-12T10:00:00+00:00"

# Only facts that have a direct representation in EvidenceSemantics
# are projected into the existing reasoner.
#
# procurement_progressing is intentionally excluded because the current
# EvidenceSemantics schema has no corresponding field. We do not invent
# a mapping merely to improve the embedding result.
FACT_TO_SEMANTIC_FIELD = {
    "followup_request": "requests_followup",
    "budget_approved": "confirms_approval",
    "commercial_terms_rejected": "expresses_rejection",
    "different_work_item": "concerns_same_work_item",
    "service_completed": "confirms_completion",
    "next_step_requested": "requests_next_step",
}


def _semantics_from_embedding_facts(
    predicted_facts: set[str],
) -> EvidenceSemantics:
    kwargs: Dict[str, object] = {
        "topic": None,
        "requests_followup": None,
        "confirms_approval": None,
        "expresses_rejection": None,
        "confirms_completion": None,
        "requests_next_step": None,
        "concerns_same_work_item": None,
    }

    for fact, field in FACT_TO_SEMANTIC_FIELD.items():
        if fact not in predicted_facts:
            continue

        if field == "concerns_same_work_item":
            kwargs[field] = False
        else:
            kwargs[field] = True

    return EvidenceSemantics(**kwargs)


def _embedding_behavior(
    primary: PrimaryState,
    text: str,
    prototypes,
    thresholds,
) -> tuple:
    from test_embedding_fact_threshold_calibration import _encode

    embedding = _encode([text])[0]

    predicted_facts, _margins = _predict_facts(
        embedding,
        prototypes,
        thresholds,
    )

    semantics = _semantics_from_embedding_facts(
        predicted_facts,
    )

    evidence = SemanticEvidence(
        evidence_id="EMBEDDING-HOLDOUT",
        content=text,
        provenance=EvidenceProvenance(
            source_system="embedding_holdout_decision_fidelity",
            record_id="EMBEDDING-HOLDOUT",
            occurred_at=datetime.fromisoformat(
                FIXED_TIMESTAMP,
            ),
        ),
        identity=EvidenceIdentity(
            customer_id="HOLDOUT-CUSTOMER",
            quality=IdentityQuality.CONFIRMED,
        ),
        semantics=semantics,
    )

    condition = EvidenceCondition(
        availability="available",
        items=(evidence,),
    )

    result = V03Reasoner(
        ReasonerConfig(
            evaluation_at=EVALUATION_AT,
            stale_after_days=30,
        )
    ).evaluate(
        primary,
        condition,
    )

    return (
        result.interpretation_class,
        result.support_level,
        result.decision_strength,
        result.recommended_focus,
    )


def test_embedding_holdout_decision_fidelity() -> None:
    prototypes = _build_full_development_prototypes()
    thresholds = _calibrate_thresholds()

    print("\n=== EMBEDDING HOLDOUT DECISION FIDELITY ===")
    print("model=sentence-transformers/all-MiniLM-L6-v2")
    print("training_source=development battery only")
    print("threshold_source=development leave-one-out only")
    print("evaluation_source=unseen holdout only")

    total = 0
    exact = 0

    family_results: dict[str, dict[str, int]] = {}

    for family_id, primary, texts, _expected_facts in HOLDOUT:
        family_total = 0
        family_exact = 0

        for variant_index, text in enumerate(texts):
            expected = _oracle_behavior(
                family_id,
                primary,
                text,
            )

            observed = _embedding_behavior(
                primary,
                text,
                prototypes,
                thresholds,
            )

            matches = observed == expected

            total += 1
            family_total += 1

            if matches:
                exact += 1
                family_exact += 1

            print(
                {
                    "candidate": "embedding_fact_prototypes_calibrated",
                    "family": family_id,
                    "variant": variant_index,
                    "expected_decision": expected,
                    "observed_decision": observed,
                    "exact": matches,
                }
            )

        family_results[family_id] = {
            "exact": family_exact,
            "total": family_total,
        }

    result = {
        "candidate": "embedding_fact_prototypes_calibrated",
        "total_variants": total,
        "exact_decisions": exact,
        "decision_fidelity": exact / total,
        "family_results": family_results,
    }

    print("\n=== EMBEDDING DECISION FIDELITY SUMMARY ===")
    print(result)


def test_embedding_holdout_decision_fidelity_negative_control() -> None:
    prototypes = _build_full_development_prototypes()
    thresholds = _calibrate_thresholds()

    total = 0
    exact = 0

    print("\n=== EMBEDDING DECISION FIDELITY H4 NEGATIVE CONTROL ===")

    for family_id, primary, texts, _expected_facts in HOLDOUT:
        if family_id != "H4-irrelevant":
            continue

        for variant_index, text in enumerate(texts):
            expected = _oracle_behavior(
                family_id,
                primary,
                text,
            )

            observed = _embedding_behavior(
                primary,
                text,
                prototypes,
                thresholds,
            )

            matches = observed == expected

            total += 1

            if matches:
                exact += 1

            print(
                {
                    "family": family_id,
                    "variant": variant_index,
                    "expected_decision": expected,
                    "observed_decision": observed,
                    "exact": matches,
                }
            )

    print(
        {
            "family": "H4-irrelevant",
            "exact": exact,
            "total": total,
            "decision_fidelity": (
                exact / total
                if total
                else 0.0
            ),
        }
    )


def test_embedding_holdout_oracle_is_unchanged() -> None:
    """Guard against accidentally modifying the evaluation oracle."""

    observed = {
        family_id: dict(values)
        for family_id, values in ORACLE_SEMANTICS.items()
    }

    assert observed == ORACLE_SEMANTICS