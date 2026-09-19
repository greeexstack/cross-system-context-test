from __future__ import annotations

import spacy


NLP = spacy.load("en_core_web_sm")

DIFFERENT_MARKERS = {
    "another",
    "different",
    "separate",
}

CURRENT_MARKERS = {
    "this",
    "current",
}


def extract_event_target(text: str) -> dict:
    doc = NLP(text)

    root = next(
        (
            token
            for token in doc
            if token.dep_ == "ROOT"
        ),
        None,
    )

    if root is None:
        return {
            "event": None,
            "target": None,
            "target_status": None,
        }

    candidates = []

    for token in doc:
        if token.dep_ in {"dobj", "pobj"}:
            candidates.append(token)

    if not candidates:
        return {
            "event": root.lemma_,
            "target": None,
            "target_status": None,
        }

    # Prefer the first main event object.
    target = candidates[0]

    status = "UNKNOWN"

    for child in target.children:
        word = child.text.lower()

        if word in DIFFERENT_MARKERS:
            status = "DIFFERENT"

        elif word in CURRENT_MARKERS:
            status = "CURRENT"

    return {
        "event": root.lemma_,
        "target": target.lemma_,
        "target_status": status,
    }