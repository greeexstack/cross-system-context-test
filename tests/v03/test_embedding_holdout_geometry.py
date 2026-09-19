from __future__ import annotations

from itertools import combinations
from typing import Dict, List

import numpy as np

from test_embedding_semantic_separation import MODEL, MODEL_NAME
from test_event_frame_holdout import HOLDOUT


def _encode(texts: List[str]) -> np.ndarray:
    return MODEL.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(a @ b)


def test_embedding_holdout_within_family_geometry() -> None:
    print("\n=== EMBEDDING HOLDOUT WITHIN-FAMILY GEOMETRY ===")
    print(f"model={MODEL_NAME}")

    for family_id, _primary, texts, _expected_facts in HOLDOUT:
        embeddings = _encode(list(texts))

        pairwise = [
            _cosine(embeddings[i], embeddings[j])
            for i, j in combinations(range(len(texts)), 2)
        ]

        print(
            {
                "family": family_id,
                "pair_count": len(pairwise),
                "mean_pair_similarity": round(float(np.mean(pairwise)), 4),
                "min_pair_similarity": round(float(np.min(pairwise)), 4),
                "max_pair_similarity": round(float(np.max(pairwise)), 4),
            }
        )


def test_embedding_holdout_cross_family_geometry() -> None:
    print("\n=== EMBEDDING HOLDOUT CROSS-FAMILY GEOMETRY ===")

    family_embeddings: Dict[str, np.ndarray] = {}

    for family_id, _primary, texts, _expected_facts in HOLDOUT:
        family_embeddings[family_id] = _encode(list(texts))

    family_ids = list(family_embeddings)

    for family_a, family_b in combinations(family_ids, 2):
        cross_family_scores = [
            _cosine(vector_a, vector_b)
            for vector_a in family_embeddings[family_a]
            for vector_b in family_embeddings[family_b]
        ]

        print(
            {
                "family_a": family_a,
                "family_b": family_b,
                "pair_count": len(cross_family_scores),
                "mean_similarity": round(float(np.mean(cross_family_scores)), 4),
                "min_similarity": round(float(np.min(cross_family_scores)), 4),
                "max_similarity": round(float(np.max(cross_family_scores)), 4),
            }
        )


def test_embedding_holdout_geometry_is_deterministic() -> None:
    samples = [
        text
        for _family_id, _primary, texts, _expected_facts in HOLDOUT
        for text in texts
    ]

    first = _encode(samples)
    second = _encode(samples)

    assert first.shape == second.shape
    assert np.allclose(first, second, atol=1e-6)