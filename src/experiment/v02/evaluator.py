from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from .engine import ReasoningResult


@dataclass(frozen=True)
class CaseScore:
    pair_id: str
    split: str
    context_sensitivity: bool
    context_resistance: bool
    direction_correctness: bool
    evidence_validity: bool
    identity_integrity: bool
    temporal_integrity: bool
    ambiguity_handling: bool
    missing_data_handling: bool
    generalization: bool
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class V02Evaluator:
    """Scores an engine against frozen metamorphic expectations.

    Ground truth is injected only into this evaluator; the reasoning engine never
    reads it. This keeps the reasoning path non-circular.
    """

    def score(self, case: dict[str, Any], base: ReasoningResult, variant: ReasoningResult, expected: dict[str, Any]) -> CaseScore:
        base_expected = expected["base_expectation"]
        variant_expected = expected["variant_expectation"]

        family = case["family_id"]
        identity_integrity = True
        ambiguity_handling = True
        temporal_integrity = True
        missing_data_handling = True

        if family in {"F05", "F06", "F07"}:
            identity_integrity = variant.identity_match == variant_expected.get("identity_match", variant.identity_match) if "identity_match" in variant_expected else variant.identity_match == base.identity_match
        if family == "F06":
            ambiguity_handling = variant.identity_match == "ambiguous_match"
        if family == "F07":
            temporal_integrity = variant.temporal_status == variant_expected.get("temporal_status")
        if family == "F08":
            missing_data_handling = variant.availability == variant_expected.get("availability") and variant.support_level == variant_expected.get("support_level")

        base_class_ok = base.interpretation_class == base_expected["interpretation_class"]
        variant_class_ok = variant.interpretation_class == variant_expected["interpretation_class"]
        base_support_ok = self._support_matches(base.support_level, base_expected["support_level"])
        variant_support_ok = self._support_matches(variant.support_level, variant_expected["support_level"])
        strength_ok = self._optional_match(variant.decision_strength, variant_expected.get("decision_strength"))

        context_sensitivity = self._sensitivity(case, base, variant, variant_expected)
        context_resistance = self._resistance(case, base, variant, variant_expected)
        if family == "F05":
            direction_correctness = variant.identity_match == "no_match" and variant.support_level == "primary_only"
        elif family == "F06":
            direction_correctness = variant.identity_match == "ambiguous_match" and variant.support_level == "primary_only"
        elif family == "F09":
            direction_correctness = variant.reversion == "toward_primary_only" and variant.support_level == "primary_only"
        else:
            direction_correctness = base_class_ok and variant_class_ok and base_support_ok and variant_support_ok and strength_ok
        evidence_validity = variant.evidence_valid and self._no_unsupported_identity_use(variant)

        generalization = case["split"] in {"development", "evaluation"} and self._workflow_generalization(case, variant)
        passed = all([
            context_sensitivity, context_resistance, direction_correctness,
            evidence_validity, identity_integrity, temporal_integrity,
            ambiguity_handling, missing_data_handling, generalization,
        ])

        return CaseScore(
            pair_id=case["pair_id"], split=case["split"],
            context_sensitivity=context_sensitivity,
            context_resistance=context_resistance,
            direction_correctness=direction_correctness,
            evidence_validity=evidence_validity,
            identity_integrity=identity_integrity,
            temporal_integrity=temporal_integrity,
            ambiguity_handling=ambiguity_handling,
            missing_data_handling=missing_data_handling,
            generalization=generalization,
            passed=passed,
        )

    @staticmethod
    def _matches(actual: Any, expected: Any) -> bool:
        return actual == expected

    @staticmethod
    def _support_matches(actual: str, expected: str) -> bool:
        if expected == "primary_only" and actual == "no_secondary_evidence":
            return True
        return actual == expected

    @staticmethod
    def _optional_match(actual: Any, expected: Any) -> bool:
        return expected is None or actual == expected

    def _sensitivity(self, case: dict[str, Any], base: ReasoningResult, variant: ReasoningResult, expected: dict[str, Any]) -> bool:
        family = case["family_id"]
        if family == "F01":
            return variant.interpretation_class != base.interpretation_class
        if family in {"F02", "F03"}:
            return variant.decision_strength != base.decision_strength
        if family == "F10":
            return variant.recommended_focus == expected.get("recommended_focus")
        return True

    def _resistance(self, case: dict[str, Any], base: ReasoningResult, variant: ReasoningResult, expected: dict[str, Any]) -> bool:
        family = case["family_id"]
        if family == "F04":
            return variant.interpretation_class == base.interpretation_class and variant.support_level == "primary_only"
        if family == "F05":
            return variant.identity_match == "no_match" and variant.interpretation_class == base.interpretation_class
        if family == "F06":
            return variant.identity_match == "ambiguous_match" and variant.interpretation_class == base.interpretation_class
        if family == "F07":
            return variant.temporal_status == "clearly_stale" and variant.support_level == "temporal_context_rejected"
        if family == "F08":
            return variant.availability == "unavailable" and variant.support_level == "safe_fallback_primary_only"
        if family == "F09":
            return variant.reversion == "toward_primary_only" and variant.support_level == "primary_only"
        return True

    @staticmethod
    def _no_unsupported_identity_use(result: ReasoningResult) -> bool:
        if result.identity_match in {"no_match", "ambiguous_match"}:
            return not result.evidence_ids
        return True

    @staticmethod
    def _workflow_generalization(case: dict[str, Any], variant: ReasoningResult) -> bool:
        if case["family_id"] != "F10":
            return True
        return case["primary"]["record_type"] == "service_order" and variant.interpretation_class == "service_completed_next_step_unrecorded"
