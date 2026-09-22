from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

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

from test_independent_replication_loader import load_suite
from test_independent_paraphrase_battery import EVALUATION_AT


V1 = "event_frame_v1"
V2 = "clause_local_v2"
HOLDOUT_AT = datetime.fromisoformat("2026-09-12T10:00:00+00:00")


def _extract(candidate: str, text: str):
    if candidate == V1:
        return CanonicalEventFrameExtractor().extract(content=text)
    if candidate == V2:
        return ClauseLocalRelationalEventFrameExtractor().extract(
            content=text,
        )
    raise ValueError(candidate)


def _oracle_semantics(case) -> EvidenceSemantics:
    values = {
        "topic": None,
        "polarity": "positive",
        "negated_concepts": (),
        "requests_followup": None,
        "expresses_acceptance": None,
        "expresses_rejection": None,
        "confirms_approval": None,
        "confirms_completion": None,
        "requests_next_step": None,
        "concerns_same_work_item": None,
    }

    for field, value in case.expected_fields:
        if field == "negated_concepts" and isinstance(value, list):
            value = tuple(value)
        values[field] = value

    return EvidenceSemantics(**values)


def _candidate_semantics(candidate: str, text: str) -> EvidenceSemantics:
    return frames_to_semantics(_extract(candidate, text).frames)


def _evaluate(case, text: str, semantics: EvidenceSemantics) -> tuple:
    evidence = SemanticEvidence(
        evidence_id=f"INDEPENDENT-{case.case_id}",
        content=text,
        provenance=EvidenceProvenance(
            source_system="independent_replication",
            record_id=case.case_id,
            occurred_at=HOLDOUT_AT,
        ),
        identity=EvidenceIdentity(
            customer_id="INDEPENDENT-REPLICATION-CUSTOMER",
            quality=IdentityQuality.CONFIRMED,
        ),
        semantics=semantics,
    )

    result = V03Reasoner(
        ReasonerConfig(
            evaluation_at=EVALUATION_AT,
            stale_after_days=30,
        )
    ).evaluate(
        PrimaryState(
            case.primary_interpretation,
            case.primary_decision_strength,
        ),
        EvidenceCondition(
            availability="available",
            items=(evidence,),
        ),
    )

    return (
        result.interpretation_class,
        result.support_level,
        result.decision_strength,
        result.recommended_focus,
    )


def _oracle_behavior(case, text: str) -> tuple:
    return _evaluate(
        case,
        text,
        _oracle_semantics(case),
    )


def _candidate_behavior(candidate: str, case, text: str) -> tuple:
    return _evaluate(
        case,
        text,
        _candidate_semantics(candidate, text),
    )


def measure(candidate: str, cases) -> dict:
    total = 0
    exact = 0
    families = {}

    for case in cases:
        family_exact = 0

        for variant_index, text in enumerate(case.texts):
            expected = _oracle_behavior(case, text)
            observed = _candidate_behavior(candidate, case, text)
            matches = observed == expected

            total += 1

            if matches:
                exact += 1
                family_exact += 1

            print(
                json.dumps(
                    {
                        "candidate": candidate,
                        "case": case.case_id,
                        "variant": variant_index,
                        "expected_decision": expected,
                        "observed_decision": observed,
                        "exact": matches,
                    },
                    sort_keys=True,
                )
            )

        families[case.case_id] = {
            "exact": family_exact,
            "total": len(case.texts),
        }

    return {
        "candidate": candidate,
        "total_variants": total,
        "exact_decisions": exact,
        "decision_fidelity": exact / total if total else 0.0,
        "family_results": families,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate frozen v1/v2 candidates against an independently "
            "supplied replication fixture."
        )
    )
    parser.add_argument(
        "--fixture",
        required=True,
        help="Path to independently authored JSON fixture.",
    )
    parser.add_argument(
        "--json-out",
        help="Optional path for the machine-readable result.",
    )
    args = parser.parse_args()

    fixture_path = Path(args.fixture)
    cases = load_suite(str(fixture_path))

    print("=== INDEPENDENT REPLICATION ===")
    print(json.dumps(
        {
            "fixture": str(fixture_path),
            "cases": len(cases),
            "variants": sum(len(case.texts) for case in cases),
        },
        sort_keys=True,
    ))

    v1 = measure(V1, cases)
    v2 = measure(V2, cases)

    result = {
        "fixture": str(fixture_path),
        "v1": v1,
        "v2": v2,
        "v2_minus_v1": (
            v2["decision_fidelity"]
            - v1["decision_fidelity"]
        ),
    }

    print("=== SUMMARY ===")
    print(json.dumps(result, indent=2, sort_keys=True))

    if args.json_out:
        output = Path(args.json_out)
        output.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())