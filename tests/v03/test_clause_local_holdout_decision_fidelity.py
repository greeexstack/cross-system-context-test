from __future__ import annotations

from datetime import datetime

from experiment.v03.clause_local_extractor_v2 import (
    ClauseLocalRelationalEventFrameExtractor,
)
from experiment.v03.event_frame_adapter import frames_to_semantics
from experiment.v03.event_frames import CanonicalEventFrameExtractor
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

from test_event_frame_holdout import HOLDOUT
from test_independent_paraphrase_battery import EVALUATION_AT


V1 = "event_frame_v1"
V2 = "clause_local_v2"


# Independently specified semantic facts for each holdout family.
#
# These are evaluation metadata only. They are never supplied to either
# extractor. The extractor sees only the holdout text.
ORACLE_SEMANTICS: dict[str, dict[str, object]] = {
    "H1-followup": {
        "topic": "proposal",
        "requests_followup": True,
        "confirms_approval": None,
        "expresses_rejection": None,
        "confirms_completion": None,
        "requests_next_step": None,
        "concerns_same_work_item": None,
    },
    "H2-supporting": {
        "topic": "proposal",
        "requests_followup": None,
        "confirms_approval": True,
        "expresses_rejection": None,
        "confirms_completion": None,
        "requests_next_step": None,
        "concerns_same_work_item": None,
    },
    "H3-contradictory": {
        "topic": "commercial_terms",
        "requests_followup": None,
        "confirms_approval": None,
        "expresses_rejection": True,
        "confirms_completion": None,
        "requests_next_step": None,
        "concerns_same_work_item": None,
    },
    "H4-irrelevant": {
        "topic": None,
        "requests_followup": None,
        "confirms_approval": None,
        "expresses_rejection": None,
        "confirms_completion": None,
        "requests_next_step": None,
        "concerns_same_work_item": False,
    },
    "H5-service-next-step": {
        "topic": "service",
        "requests_followup": None,
        "confirms_approval": None,
        "expresses_rejection": None,
        "confirms_completion": True,
        "requests_next_step": True,
        "concerns_same_work_item": None,
    },
}


def _extract_v1(text: str):
    return CanonicalEventFrameExtractor().extract(
        content=text,
    )


def _extract_v2(text: str):
    return ClauseLocalRelationalEventFrameExtractor().extract(
        content=text,
    )


def _evaluate(
    primary: PrimaryState,
    text: str,
    semantics: EvidenceSemantics,
) -> tuple:
    evidence = SemanticEvidence(
        evidence_id="HOLDOUT",
        content=text,
        provenance=EvidenceProvenance(
            source_system="decision_fidelity_holdout",
            record_id="HOLDOUT",
            occurred_at=datetime.fromisoformat(
                "2026-09-12T10:00:00+00:00"
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


def _semantics_from_candidate(
    candidate: str,
    text: str,
) -> EvidenceSemantics:
    if candidate == V1:
        frames = _extract_v1(text).frames
    elif candidate == V2:
        frames = _extract_v2(text).frames
    else:
        raise ValueError(candidate)

    return frames_to_semantics(frames)


def _oracle_semantics_for(
    family_id: str,
) -> EvidenceSemantics:
    return EvidenceSemantics(
        **ORACLE_SEMANTICS[family_id],
    )


def _oracle_behavior(
    family_id: str,
    primary: PrimaryState,
    text: str,
) -> tuple:
    return _evaluate(
        primary,
        text,
        _oracle_semantics_for(family_id),
    )


def _candidate_behavior(
    candidate: str,
    primary: PrimaryState,
    text: str,
) -> tuple:
    return _evaluate(
        primary,
        text,
        _semantics_from_candidate(
            candidate,
            text,
        ),
    )


def _measure_decision_fidelity(
    candidate: str,
) -> dict[str, object]:
    total = 0
    exact = 0

    family_results: dict[str, dict[str, int]] = {}

    for family_id, primary, texts, _expected_facts in HOLDOUT:
        family_exact = 0
        family_total = 0

        for variant_index, text in enumerate(texts):
            total += 1
            family_total += 1

            expected = _oracle_behavior(
                family_id,
                primary,
                text,
            )

            observed = _candidate_behavior(
                candidate,
                primary,
                text,
            )

            matches = observed == expected

            if matches:
                exact += 1
                family_exact += 1

            print(
                {
                    "candidate": candidate,
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

    return {
        "candidate": candidate,
        "total_variants": total,
        "exact_decisions": exact,
        "decision_fidelity": exact / total,
        "family_results": family_results,
    }


def test_holdout_decision_fidelity_v1_vs_v2() -> None:
    print("\n=== HOLDOUT DECISION FIDELITY ===")

    v1 = _measure_decision_fidelity(V1)
    v2 = _measure_decision_fidelity(V2)

    print(v1)
    print(v2)

    print(
        {
            "metric": "decision_fidelity",
            "v1": v1["decision_fidelity"],
            "v2": v2["decision_fidelity"],
            "v2_minus_v1": (
                v2["decision_fidelity"]
                - v1["decision_fidelity"]
            ),
        }
    )

    assert v1["total_variants"] == 20
    assert v2["total_variants"] == 20


def test_holdout_decision_fidelity_is_measured_per_family() -> None:
    for candidate in (V1, V2):
        result = _measure_decision_fidelity(candidate)

        assert set(result["family_results"]) == {
            "H1-followup",
            "H2-supporting",
            "H3-contradictory",
            "H4-irrelevant",
            "H5-service-next-step",
        }

        assert sum(
            family["total"]
            for family in result["family_results"].values()
        ) == 20


def test_holdout_oracle_decisions_are_deterministic() -> None:
    first = [
        _oracle_behavior(
            family_id,
            primary,
            texts[0],
        )
        for family_id, primary, texts, _expected_facts in HOLDOUT
    ]

    second = [
        _oracle_behavior(
            family_id,
            primary,
            texts[0],
        )
        for family_id, primary, texts, _expected_facts in HOLDOUT
    ]

    assert first == second