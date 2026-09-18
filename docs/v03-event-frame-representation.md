# v0.3 Experimental Event-Frame Representation

## Status

Candidate representation design.

This is an experimental intermediate representation.
It must not be described as genuine natural-language understanding.

---

## 1. Problem being addressed

The independent paraphrase battery found:

    15 controlled pairs
    7 behavioral inconsistencies
    8 semantic-representation drifts
    0 metadata drifts

The current representation is a collection of phrase-triggered boolean
attributes.

The redesign therefore targets representation stability rather than adding
more answer-specific decision rules.

---

## 2. Representation goal

Raw evidence should be converted into factual event frames.

Conceptually:

    raw observation
        ->
    factual event frame(s)
        ->
    validation
        ->
    reasoning

The frame describes what the evidence asserts.

It must not encode the expected business decision.

---

## 3. Candidate frame

A factual frame contains:

    actor
    action
    object
    state
    polarity
    temporal_reference
    relevance

Not every field must be populated for every observation.

Unknown information remains unknown.

Absence of evidence must not be converted into a factual negative assertion.

---

## 4. Example mappings

### Follow-up request

Text:

    The buyer wants another discussion next Thursday.

Frame:

    actor = customer
    action = request
    object = followup_conversation
    state = requested
    polarity = positive
    temporal_reference = next_thursday
    relevance = same_work_item

### Budget approval

Text:

    Funding for the quoted amount is authorized.

Frame:

    actor = customer
    action = confirm
    object = quote
    state = budget_approved
    polarity = positive

### Commercial rejection

Text:

    The customer will not accept the revised conditions.

Frame:

    actor = customer
    action = accept
    object = commercial_terms
    state = rejected
    polarity = negative

### Service completion + next step

Text:

    The implementation workshop is complete and the customer asks
    about the next handoff.

Frames:

    actor = customer
    action = confirm
    object = service
    state = completed
    polarity = positive

    actor = customer
    action = request
    object = handoff
    state = next_step
    polarity = positive

### Irrelevant evidence

Text:

    The conversation concerns another location rollout.

Frame:

    relevance = different_work_item

This is factual evidence about relevance, not an answer label.

---

## 5. What the frame must NOT contain

Forbidden:

    expected_transition
    ground_truth
    benchmark_family
    pair_id
    support_level
    interpretation_class
    decision_strength
    recommendation
    finding

Those belong downstream or to evaluation.

---

## 6. Provenance separation

The frame is not a replacement for provenance.

Evidence remains:

    evidence
        content
        provenance
        identity
        availability
        frame(s)

Identity, timestamp, source, and availability are validated independently.

---

## 7. Unknown versus false

The representation must distinguish:

    true assertion
    explicit negative assertion
    unknown / not established

For example:

    customer accepts quote

must not become:

    false

merely because the text contains no acceptance statement.

This distinction is mandatory for the redesign.

---

## 8. Compatibility

The existing reasoner may temporarily consume an adapter-produced
EvidenceSemantics representation.

The long-term direction is:

    frame representation
        ->
    reasoning

The adapter exists only to isolate the experiment from unrelated
v0.3 contracts.

---

## 9. Non-circularity

Frame extraction must not receive:

    expected labels
    scenario IDs
    pair IDs
    hidden ground truth
    expected transitions

The independent paraphrase battery remains an external measurement.

---

## 10. Experimental criterion

The redesign should be rerun against the independent battery.

Primary measurements:

    representation invariance
    behavioral consistency
    negative-control resistance

A redesign succeeds empirically only if it improves measured robustness
without introducing unsupported changes in the negative controls.

No numerical acceptance threshold is established yet.