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
from experiment.v03.spacy_dependency_extractor import (
    SpacyDependencyEventFrameExtractor,
)

from test_event_frame_holdout import HOLDOUT
from test_independent_paraphrase_battery import EVALUATION_AT


V1 = "event_frame_v1"
V2 = "clause_local_v2"
SPACY = "spacy_dependency"


ORACLE_SEMANTICS: dict[str, dict[str, object]] = {
    "H1-followup": {
        "topic": "proposal",
        "requests_followup": True,
        "expresses_acceptance": None,
        "expresses_rejection": None,
        "confirms_approval": None,
        "confirms_completion": None,
        "requests_next_step": None,
        "concerns_same_work_item": None,
    },
    "H2-supporting": {
        "topic": "proposal",
        "requests_followup": None,
        "expresses_acceptance": None,
        "expresses_rejection": None,
        "confirms_approval": True,
        "confirms_completion": None,
        "requests_next_step": None,
        "concerns_same_work_item": None,
    },
    "H3-contradictory": {
        "topic": "commercial_terms",
        "requests_followup": None,
        "expresses_acceptance": None,
        "expresses_rejection": True,
        "confirms_approval": None,
        "confirms_completion": None,
        "requests_next_step": None,
        "concerns_same_work_item": None,
    },
    "H4-irrelevant": {
        "topic": None,
        "requests_followup": None,
        "expresses_acceptance": None,
        "expresses_rejection": None,
        "confirms_approval": None,
        "confirms_completion": None,
        "requests_next_step": None,
        "concerns_same_work_item": False,
    },
    "H5-service-next-step": {
        "topic": "service",
        "requests_followup": None,
        "expresses_acceptance": None,
        "expresses_rejection": None,
        "confirms_approval": None,
        "confirms_completion": True,
        "requests_next_step": True,
        "concerns_same_work_item": None,
    },
}


def _extract(candidate: str, text: str):
    if candidate == V1:
        return CanonicalEventFrameExtractor().extract(
            content=text,
        )

    if candidate == V2:
        return ClauseLocalRelationalEventFrameExtractor().extract(
            content=text,
        )

    if candidate == SPACY:
        return SpacyDependencyEventFrameExtractor().extract(
            content=text,
        )

    raise ValueError(candidate)


def _core_facts(frames) -> set[str]:
    facts: set[str] = set()

    for frame in frames:
        if (
            frame.action == "request"
            and frame.object == "followup_conversation"
            and frame.state == "requested"
            and frame.polarity.value == "positive"
        ):
            facts.add("followup_request")

        if (
            frame.action == "confirm"
            and frame.object == "quote"
            and frame.state == "budget_approved"
            and frame.polarity.value == "positive"
        ):
            facts.add("budget_approved")

        if (
            frame.action == "report"
            and frame.object == "procurement"
            and frame.state == "progressing"
            and frame.polarity.value == "positive"
        ):
            facts.add("procurement_progressing")

        if (
            frame.action == "accept"
            and frame.object == "commercial_terms"
            and frame.state == "rejected"
            and frame.polarity.value == "negative"
        ):
            facts.add("commercial_terms_rejected")

        if (
            frame.action == "confirm"
            and frame.object == "service"
            and frame.state == "completed"
            and frame.polarity.value == "positive"
        ):
            facts.add("service_completed")

        if (
            frame.action == "request"
            and frame.object in {"handoff", "next_step"}
            and frame.state == "next_step"
            and frame.polarity.value == "positive"
        ):
            facts.add("next_step_requested")

        if frame.relevance == "different_work_item":
            facts.add("different_work_item")

    return facts


def _evaluate(
    primary: PrimaryState,
    text: str,
    frames,
) -> tuple:
    semantics = frames_to_semantics(frames)

    evidence = SemanticEvidence(
        evidence_id="HOLDOUT",
        content=text,
        provenance=EvidenceProvenance(
            source_system="spacy_holdout_comparison",
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


def _candidate_behavior(
    candidate: str,
    primary: PrimaryState,
    text: str,
) -> tuple:
    frames = _extract(candidate, text).frames
    return _evaluate(
        primary,
        text,
        frames,
    )


def _oracle_behavior(
    family_id: str,
    primary: PrimaryState,
    text: str,
) -> tuple:
    semantics = EvidenceSemantics(
        **ORACLE_SEMANTICS[family_id],
    )

    evidence = SemanticEvidence(
        evidence_id="HOLDOUT-ORACLE",
        content=text,
        provenance=EvidenceProvenance(
            source_system="spacy_holdout_oracle",
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


def _factual_accuracy(candidate: str) -> dict[str, object]:
    exact = 0
    partial = 0
    non_exact = 0
    false_positive_variants = 0
    total = 0

    by_family: dict[str, dict[str, int]] = {}

    for family_id, primary, texts, expected_facts in HOLDOUT:
        del primary

        complete = 0
        family_partial = 0
        family_non_exact = 0

        for text in texts:
            total += 1

            observed = _core_facts(
                _extract(candidate, text).frames,
            )

            missing = expected_facts - observed
            extra = observed - expected_facts

            if not missing and not extra:
                exact += 1
                complete += 1
            elif expected_facts.intersection(observed) and not extra:
                partial += 1
                family_partial += 1
            else:
                non_exact += 1
                family_non_exact += 1

            if extra:
                false_positive_variants += 1

        by_family[family_id] = {
            "exact": complete,
            "partial": family_partial,
            "non_exact": family_non_exact,
        }

    return {
        "candidate": candidate,
        "total": total,
        "exact": exact,
        "partial": partial,
        "non_exact": non_exact,
        "exact_rate": exact / total,
        "false_positive_variants": false_positive_variants,
        "by_family": by_family,
    }


def _behavioral_consistency(candidate: str) -> dict[str, object]:
    total_pairs = 0
    consistent = 0

    by_family: dict[str, dict[str, int]] = {}

    for family_id, primary, texts, _expected_facts in HOLDOUT:
        baseline = _candidate_behavior(
            candidate,
            primary,
            texts[0],
        )

        family_consistent = 0
        family_inconsistent = 0

        for text in texts[1:]:
            total_pairs += 1

            variant = _candidate_behavior(
                candidate,
                primary,
                text,
            )

            if variant == baseline:
                consistent += 1
                family_consistent += 1
            else:
                family_inconsistent += 1

        by_family[family_id] = {
            "consistent": family_consistent,
            "inconsistent": family_inconsistent,
        }

    return {
        "candidate": candidate,
        "total_pairs": total_pairs,
        "consistent": consistent,
        "inconsistent": total_pairs - consistent,
        "consistency_rate": consistent / total_pairs,
        "by_family": by_family,
    }


def _decision_fidelity(candidate: str) -> dict[str, object]:
    total = 0
    exact = 0

    by_family: dict[str, dict[str, int]] = {}

    for family_id, primary, texts, _expected_facts in HOLDOUT:
        family_exact = 0

        for text in texts:
            total += 1

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

            if observed == expected:
                exact += 1
                family_exact += 1

        by_family[family_id] = {
            "exact": family_exact,
            "total": 4,
        }

    return {
        "candidate": candidate,
        "total": total,
        "exact": exact,
        "fidelity": exact / total,
        "by_family": by_family,
    }


def _negative_control(candidate: str) -> dict[str, object]:
    family = next(
        item
        for item in HOLDOUT
        if item[0] == "H4-irrelevant"
    )

    family_id, primary, texts, _expected_facts = family

    states = [
        _candidate_behavior(
            candidate,
            primary,
            text,
        )
        for text in texts
    ]

    consistent = sum(
        state == states[0]
        for state in states[1:]
    )

    return {
        "candidate": candidate,
        "family": family_id,
        "pairs": 3,
        "consistent": consistent,
        "rate": consistent / 3,
    }


def test_three_way_holdout_factual_comparison() -> None:
    results = {
        candidate: _factual_accuracy(candidate)
        for candidate in (V1, V2, SPACY)
    }

    print("\n=== THREE-WAY HOLDOUT FACTUAL ACCURACY ===")

    for candidate, result in results.items():
        print(result)

    print(
        {
            candidate: result["exact_rate"]
            for candidate, result in results.items()
        }
    )

    assert all(
        result["total"] == 20
        for result in results.values()
    )


def test_three_way_holdout_behavioral_comparison() -> None:
    results = {
        candidate: _behavioral_consistency(candidate)
        for candidate in (V1, V2, SPACY)
    }

    print("\n=== THREE-WAY HOLDOUT BEHAVIORAL CONSISTENCY ===")

    for candidate, result in results.items():
        print(result)

    print(
        {
            candidate: result["consistency_rate"]
            for candidate, result in results.items()
        }
    )

    assert all(
        result["total_pairs"] == 15
        for result in results.values()
    )


def test_three_way_holdout_decision_fidelity() -> None:
    results = {
        candidate: _decision_fidelity(candidate)
        for candidate in (V1, V2, SPACY)
    }

    print("\n=== THREE-WAY HOLDOUT DECISION FIDELITY ===")

    for candidate, result in results.items():
        print(result)

    print(
        {
            candidate: result["fidelity"]
            for candidate, result in results.items()
        }
    )

    assert all(
        result["total"] == 20
        for result in results.values()
    )


def test_three_way_holdout_negative_control() -> None:
    results = {
        candidate: _negative_control(candidate)
        for candidate in (V1, V2, SPACY)
    }

    print("\n=== THREE-WAY HOLDOUT NEGATIVE CONTROL ===")

    for candidate, result in results.items():
        print(result)

    assert all(
        result["pairs"] == 3
        for result in results.values()
    )


def test_three_way_holdout_comparison_is_deterministic() -> None:
    first = {
        candidate: (
            _factual_accuracy(candidate),
            _behavioral_consistency(candidate),
            _decision_fidelity(candidate),
            _negative_control(candidate),
        )
        for candidate in (V1, V2, SPACY)
    }

    second = {
        candidate: (
            _factual_accuracy(candidate),
            _behavioral_consistency(candidate),
            _decision_fidelity(candidate),
            _negative_control(candidate),
        )
        for candidate in (V1, V2, SPACY)
    }

    assert first == second
