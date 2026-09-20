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

TARGET_COMPLEMENT_PREPOSITIONS = {
    "focus": {"on"},
}

SUBJECT_TARGET_PREDICATES = {
    "concern",
    "relate",
    "involve",
}


def _status(token):
    # Status belongs to the target noun phrase itself.
    # Only inspect the target's direct modifiers so markers
    # from nested arguments cannot bleed into this argument.
    modifiers = {
        child.text.lower()
        for child in token.children
    }

    if modifiers & DIFFERENT_MARKERS:
        return "DIFFERENT"

    if modifiers & CURRENT_MARKERS:
        return "CURRENT"

    return "UNKNOWN"


def _noun_relation(token):
    if token.dep_ == "dobj":
        return {
            "relation": "object",
            "target": token.lemma_,
            "status": _status(token),
        }

    if token.dep_ == "pobj":
        return {
            "relation": f"prep:{token.head.text.lower()}",
            "target": token.lemma_,
            "status": _status(token),
        }

    return None


def _prepositional_target(root):
    allowed_prepositions = (
        TARGET_COMPLEMENT_PREPOSITIONS.get(root.lemma_)
    )

    if not allowed_prepositions:
        return None

    for child in root.children:
        if (
            child.dep_ == "prep"
            and child.text.lower() in allowed_prepositions
        ):
            for descendant in child.children:
                if descendant.dep_ == "pobj":
                    return descendant

    return None


def _subject_target(root):
    if root.lemma_ not in SUBJECT_TARGET_PREDICATES:
        return None

    for child in root.children:
        if child.dep_ == "nsubj":
            return child

    return None


def _event_arguments(event_token):
    relations = []

    for child in event_token.children:
        if child.dep_ == "dobj":
            relation = _noun_relation(child)

            if relation is not None:
                relations.append(relation)

        elif child.dep_ == "prep":
            for descendant in child.children:
                if descendant.dep_ == "pobj":
                    relations.append(
                        {
                            "relation":
                                f"prep:{child.text.lower()}",
                            "target":
                                descendant.lemma_,
                            "status":
                                _status(descendant),
                        }
                    )

    return relations


def _subevents(event_token):
    events = []

    for token in event_token.doc:
        if token is event_token:
            continue

        if token.pos_ != "VERB":
            continue

        if token.dep_ not in {
            "pcomp",
            "advcl",
            "ccomp",
            "xcomp",
            "relcl",
        }:
            continue

        events.append(
            {
                "event": token.lemma_,
                "relation_to_parent":
                    token.dep_,
                "arguments":
                    _event_arguments(token),
            }
        )

    return events


def extract_event_frame(text: str) -> dict:
    doc = NLP(text)

    root = next(
        (
            token
            for token in doc
            if token.dep_ == "ROOT"
            and token.pos_ == "VERB"
        ),
        None,
    )

    if root is None:
        return {
            "event": None,
            "arguments": [],
            "subevents": [],
        }

    arguments = _event_arguments(root)

    # Predicates such as "focus on X" use a
    # prepositional complement as their target.
    complement_target = _prepositional_target(root)

    if complement_target is not None:
        arguments.append(
            {
                "relation":
                    f"prep:{complement_target.head.text.lower()}",
                "target":
                    complement_target.lemma_,
                "status":
                    _status(complement_target),
            }
        )

    # Predicates such as "concern X" / "relate to X" /
    # "involve X" can use their grammatical subject
    # as the work-item target.
    subject_target = _subject_target(root)

    if subject_target is not None:
        arguments.append(
            {
                "relation": "subject_target",
                "target": subject_target.lemma_,
                "status": _status(subject_target),
            }
        )

    # Passive voice: the grammatical subject is the
    # thing being acted upon.
    passive_targets = [
        token
        for token in doc
        if token.dep_ == "nsubjpass"
    ]

    if passive_targets:
        passive_target = passive_targets[0]

        arguments.append(
            {
                "relation": "passive_subject",
                "target": passive_target.lemma_,
                "status": _status(passive_target),
            }
        )

    # Capture additional prepositional relations,
    # including prepositions attached to noun arguments.
    seen = {
        (
            relation["relation"],
            relation["target"],
        )
        for relation in arguments
    }

    for token in doc:
        if token.dep_ != "prep":
            continue

        for descendant in token.children:
            if descendant.dep_ != "pobj":
                continue

            relation = {
                "relation":
                    f"prep:{token.text.lower()}",
                "target":
                    descendant.lemma_,
                "status":
                    _status(descendant),
                "attached_to":
                    token.head.lemma_,
            }

            key = (
                relation["relation"],
                relation["target"],
            )

            if key not in seen:
                arguments.append(relation)
                seen.add(key)

    return {
        "event": root.lemma_,
        "arguments": arguments,
        "subevents": _subevents(root),
    }