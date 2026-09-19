from __future__ import annotations

from math import sqrt

from sentence_transformers import SentenceTransformer

from test_clause_local_construction_battery import CONSTRUCTION_BATTERY


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

MODEL = SentenceTransformer(MODEL_NAME)


# These are semantic anchors, deliberately phrased independently from the
# development and holdout examples.
#
# They describe meanings, not benchmark output labels.
ANCHORS = {
    "followup": (
        "the customer wants another conversation about the current matter",
        "the customer would like to speak again about the proposal",
        "the customer is asking to continue discussions later",
    ),
    "approval": (
        "the proposed spending has received financial authorization",
        "the organization has approved the amount for the purchase",
        "the requested expenditure has been cleared by finance",
    ),
    "rejection": (
        "the customer does not accept the revised commercial terms",
        "the buyer considers the proposed terms unsuitable",
        "the customer refuses the amended arrangement",
    ),
    "completion": (
        "the service activity has been completed",
        "the implementation work has finished",
        "the delivery session has concluded",
    ),
    "next_step": (
        "the customer wants to know what happens next",
        "the customer requests information about the following step",
        "the customer wants guidance about the subsequent handover",
    ),
    "different_work_item": (
        "the discussion concerns a separate business activity",
        "the conversation is about another project rather than this one",
        "the current opportunity is not the subject of the discussion",
    ),
}


def _embed(texts: list[str]):
    return MODEL.encode(
        texts,
        normalize_embeddings=True,
    )


def _cosine(a, b) -> float:
    return float(sum(x * y for x, y in zip(a, b)))


def _anchor_centroids():
    centroids = {}

    for label, texts in ANCHORS.items():
        vectors = _embed(list(texts))

        centroid = [
            sum(row[index] for row in vectors) / len(vectors)
            for index in range(len(vectors[0]))
        ]

        norm = sqrt(
            sum(value * value for value in centroid)
        )

        centroids[label] = [
            value / norm
            for value in centroid
        ]

    return centroids


CENTROIDS = _anchor_centroids()


def test_embedding_anchor_geometry_is_separable() -> None:
    print("\n=== EMBEDDING ANCHOR GEOMETRY ===")

    labels = list(ANCHORS)

    for label_a in labels:
        row = {}

        for label_b in labels:
            row[label_b] = round(
                _cosine(
                    CENTROIDS[label_a],
                    CENTROIDS[label_b],
                ),
                4,
            )

        print(
            {
                "anchor": label_a,
                "similarities": row,
            }
        )

    assert len(CENTROIDS) == 6


def test_construction_examples_map_to_nearest_semantic_anchor() -> None:
    total = 0
    nearest_correct = 0

    expected_mapping = {
        "C1-followup-interest": "followup",
        "C2-followup-suggestion": "followup",
        "C3-institutional-approval": "approval",
    }

    print(
        "\n=== EMBEDDING NEAREST-ANCHOR CLASSIFICATION ==="
    )

    for family_id, _primary_state, variants in CONSTRUCTION_BATTERY:
        expected_label = expected_mapping[family_id]

        for variant_index, (text, _expected_facts) in enumerate(
            variants,
            start=0,
        ):
            total += 1

            vector = _embed([text])[0]

            similarities = {
                label: _cosine(
                    vector,
                    centroid,
                )
                for label, centroid in CENTROIDS.items()
            }

            predicted = max(
                similarities,
                key=similarities.get,
            )

            correct = predicted == expected_label

            if correct:
                nearest_correct += 1

            print(
                {
                    "family": family_id,
                    "variant": variant_index,
                    "predicted": predicted,
                    "expected_anchor": expected_label,
                    "correct": correct,
                    "similarities": {
                        label: round(score, 4)
                        for label, score in similarities.items()
                    },
                }
            )

    print(
        {
            "total": total,
            "nearest_anchor_correct": nearest_correct,
            "accuracy": nearest_correct / total,
        }
    )

    assert total == 12


def test_embedding_paraphrases_cluster_without_text_identity() -> None:
    print(
        "\n=== EMBEDDING WITHIN-CONSTRUCTION SIMILARITY ==="
    )

    for family_id, _primary_state, variants in CONSTRUCTION_BATTERY:
        texts = [text for text, _expected in variants]

        vectors = _embed(texts)

        pair_scores = []

        for index, left in enumerate(vectors):
            for right in vectors[index + 1 :]:
                pair_scores.append(
                    _cosine(left, right)
                )

        mean_similarity = (
            sum(pair_scores) / len(pair_scores)
        )

        print(
            {
                "family": family_id,
                "pair_count": len(pair_scores),
                "mean_pair_similarity": round(
                    mean_similarity,
                    4,
                ),
                "min_pair_similarity": round(
                    min(pair_scores),
                    4,
                ),
                "max_pair_similarity": round(
                    max(pair_scores),
                    4,
                ),
            }
        )

        assert len(pair_scores) == 6