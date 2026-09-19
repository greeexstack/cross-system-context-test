from __future__ import annotations

import pytest
import spacy

from test_embedding_dwi_role_reversal_battery import CASES


NLP = spacy.load("en_core_web_sm")


def _describe(doc):
    objects = []

    for token in doc:
        if token.dep_ in {"obj", "dobj", "pobj", "obl"}:
            objects.append(
                {
                    "text": token.text,
                    "dep": token.dep_,
                    "head": token.head.text,
                    "head_dep": token.head.dep_,
                    "pos": token.pos_,
                    "children": [
                        {
                            "text": child.text,
                            "dep": child.dep_,
                            "pos": child.pos_,
                        }
                        for child in token.children
                    ],
                }
            )

    noun_chunks = []

    for chunk in doc.noun_chunks:
        noun_chunks.append(
            {
                "text": chunk.text,
                "root": chunk.root.text,
                "root_dep": chunk.root.dep_,
                "root_head": chunk.root.head.text,
                "tokens": [
                    (token.text, token.dep_, token.pos_)
                    for token in chunk
                ],
            }
        )

    return {
        "root": [
            token.text
            for token in doc
            if token.dep_ == "ROOT"
        ],
        "objects": objects,
        "noun_chunks": noun_chunks,
        "key_tokens": [
            {
                "text": token.text,
                "dep": token.dep_,
                "head": token.head.text,
                "pos": token.pos_,
            }
            for token in doc
            if token.text.lower()
            in {
                "this",
                "another",
                "different",
                "separate",
                "not",
            }
        ],
    }


@pytest.mark.parametrize(
    "pair_id,current_item,different_item",
    CASES,
)
def test_dependency_role_inspection(
    pair_id: str,
    current_item: str,
    different_item: str,
):
    current_doc = NLP(current_item)
    different_doc = NLP(different_item)

    print(f"\n=== {pair_id} ===")

    print("\nCURRENT:")
    print(current_item)
    print(_describe(current_doc))

    print("\nDIFFERENT:")
    print(different_item)
    print(_describe(different_doc))


def test_battery_size():
    assert len(CASES) == 8