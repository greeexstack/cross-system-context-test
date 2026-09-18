# v0.3 Semantic Representation Invariant

## Purpose

This document defines the machine-checkable representation invariant that
the v0.3 redesign must satisfy before it can be considered robust to
semantics-preserving wording changes.

The invariant is derived from the measured independent paraphrase battery.

---

## 1. Core invariant

Given an original evidence observation O and a paraphrase P such that:

- the underlying observable fact is unchanged;
- identity is unchanged;
- timestamp is unchanged;
- provenance is unchanged;
- source availability is unchanged;
- evidentiary relationship is unchanged;

then:

```text
semantic(O) == semantic(P)