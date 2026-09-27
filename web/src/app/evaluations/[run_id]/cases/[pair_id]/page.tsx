"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  getCase,
  type CaseResult,
  type EvidenceItem,
  type ReasoningSnapshot,
} from "@/lib/api";

function formatValue(value: string | null) {
  if (!value) {
    return "Not specified";
  }

  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function supportSummary(value: string | null) {
  switch (value) {
    case "no_secondary_evidence":
      return "No supporting evidence was available.";

    case "primary_only":
      return "The primary information remained the basis of the result.";

    case "secondary_supported":
      return "Additional context supported the existing interpretation.";

    case "supported_by_secondary_context":
      return "Additional context provided relevant supporting evidence.";

    case "weakened_by_secondary_context":
      return "Additional context weakened the existing interpretation.";

    case "mixed_evidence":
      return "The additional evidence contained mixed signals.";

    case "temporal_context_rejected":
      return "The evidence was identified but was too old to treat as current.";

    case "safe_fallback_primary_only":
      return "The secondary source was unavailable, so the primary interpretation was preserved.";

    default:
      return formatValue(value);
  }
}

function interpretationSummary(value: string | null) {
  switch (value) {
    case "quote_pending_decision":
      return "The opportunity remained a pending decision.";

    case "quote_followup_pending":
      return "The additional context supported a follow-up interpretation.";

    case "negotiation_open":
      return "The negotiation remained open.";

    case "service_completed_next_step_unrecorded":
      return "The service was completed, but the next step was not recorded.";

    default:
      return formatValue(value);
  }
}

function checkLabel(name: string) {
  const labels: Record<string, string> = {
    context_sensitivity: "Context sensitivity",
    context_resistance: "Context resistance",
    direction_correctness: "Expected direction",
    evidence_validity: "Evidence validity",
    identity_integrity: "Subject identity",
    temporal_integrity: "Information timing",
    ambiguity_handling: "Ambiguity handling",
    missing_data_handling: "Missing information",
    generalization: "Generalization",
  };

  return labels[name] ?? formatValue(name);
}

function checkDescription(name: string) {
  const descriptions: Record<string, string> = {
    context_sensitivity:
      "Relevant context should produce the expected change in the result.",

    context_resistance:
      "Irrelevant or invalid context should not create an unsupported change.",

    direction_correctness:
      "The observed transition should follow the expected direction for this case.",

    evidence_validity:
      "The evidence used by the case should satisfy its validity requirements.",

    identity_integrity:
      "Evidence should belong to the subject being evaluated.",

    temporal_integrity:
      "Evidence timing should be handled according to the case requirements.",

    ambiguity_handling:
      "Ambiguous evidence should not be treated as more certain than the case allows.",

    missing_data_handling:
      "Missing information should result in a safe, explicit outcome.",

    generalization:
      "The case should satisfy the generalization requirement defined for it.",
  };

  return (
    descriptions[name] ??
    "This validation check passed for the case."
  );
}

function getChangeSummary(item: CaseResult) {
  const interpretationChanged =
    item.base.interpretation_class !==
    item.variant.interpretation_class;

  const supportChanged =
    item.base.support_level !==
    item.variant.support_level;

  const strengthChanged =
    item.base.decision_strength !==
    item.variant.decision_strength;

  if (interpretationChanged) {
    return {
      title: "The interpretation changed.",
      description:
        "The result with additional context recorded a different interpretation from the primary-only state.",
    };
  }

  if (supportChanged && strengthChanged) {
    return {
      title: "The interpretation stayed the same, but its support changed.",
      description:
        "The additional context affected both the supporting-information state and the recorded decision strength.",
    };
  }

  if (supportChanged) {
    return {
      title: "The interpretation stayed the same, but the support changed.",
      description:
        "The additional context changed how much supporting information was recorded without changing the interpretation class.",
    };
  }

  if (strengthChanged) {
    return {
      title: "The interpretation stayed the same, but the decision strength changed.",
      description:
        "The additional context changed the recorded decision strength without changing the interpretation class.",
    };
  }

  return {
    title: "The recorded interpretation remained the same.",
    description:
      "The additional context did not produce a different interpretation or decision strength in this case.",
  };
}

function evidenceLabel(item: EvidenceItem) {
  const direction =
    item.direction === "inbound"
      ? "Incoming"
      : item.direction === "outbound"
        ? "Outgoing"
        : formatValue(item.direction);

  return `${direction} ${formatValue(item.channel)}`;
}

function EvidenceList({
  snapshot,
  emptyMessage,
}: {
  snapshot: ReasoningSnapshot;
  emptyMessage: string;
}) {
  if (snapshot.evidence.length === 0) {
    return (
      <div className="evidence-empty">
        <span>No evidence records were used.</span>
        <p>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="evidence-record-list">
      {snapshot.evidence.map((evidence) => (
        <article
          key={evidence.evidence_id}
          className="evidence-record"
        >
          <div className="evidence-record-top">
            <div>
              <span className="evidence-record-id">
                {evidence.evidence_id}
              </span>

              <strong>{evidence.subject}</strong>
            </div>

            <span className="evidence-record-type">
              {evidenceLabel(evidence)}
            </span>
          </div>

          <p className="evidence-record-summary">
            {evidence.summary}
          </p>

          <div className="evidence-record-meta">
            <span>
              {formatDate(evidence.occurred_at)}
            </span>
          </div>
        </article>
      ))}
    </div>
  );
}

function NotesList({
  notes,
}: {
  notes: string[];
}) {
  if (notes.length === 0) {
    return null;
  }

  return (
    <div className="note-block">
      <span>Engine notes</span>

      <div className="note-list">
        {notes.map((note, index) => (
          <p key={`${note}-${index}`}>
            {note}
          </p>
        ))}
      </div>
    </div>
  );
}

export default function CasePage({
  params,
}: {
  params: Promise<{
    run_id: string;
    pair_id: string;
  }>;
}) {
  const [runId, setRunId] = useState("");
  const [pairId, setPairId] = useState("");
  const [item, setItem] = useState<CaseResult | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    params.then(({ run_id, pair_id }) => {
      setRunId(run_id);
      setPairId(pair_id);

      getCase(run_id, pair_id)
        .then(setItem)
        .catch((err) => {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load this case.",
          );
        });
    });
  }, [params]);

  const changeSummary = useMemo(() => {
    if (!item) {
      return null;
    }

    return getChangeSummary(item);
  }, [item]);

  if (error) {
    return (
      <main className="site-shell">
        <nav className="nav">
          <Link href="/" className="logo">
            <span className="logo-mark">C</span>
            <span className="logo-name">
              Cross-System Context
            </span>
          </Link>
        </nav>

        <section className="empty-state">
          <div className="section-kicker">
            CASE UNAVAILABLE
          </div>

          <h1>
            We could not load this case.
          </h1>

          <p>{error}</p>

          <Link
            href={`/evaluations/${runId}`}
            className="button button-primary"
          >
            Back to result
          </Link>
        </section>
      </main>
    );
  }

  if (!item || !changeSummary) {
    return (
      <main className="site-shell">
        <nav className="nav">
          <Link href="/" className="logo">
            <span className="logo-mark">C</span>
            <span className="logo-name">
              Cross-System Context
            </span>
          </Link>
        </nav>

        <section className="loading-state">
          <div className="loader-ring" />
          <span>Loading case...</span>
        </section>
      </main>
    );
  }

  return (
    <main className="site-shell">
      <nav className="nav">
        <Link href="/" className="logo">
          <span className="logo-mark">C</span>
          <span className="logo-name">
            Cross-System Context
          </span>
        </Link>

        <div className="nav-links">
          <Link href="/evaluate">Evaluations</Link>
          <Link href="/integrate">Integrate</Link>
        </div>
      </nav>

      <section className="case-page-header">
        <Link
          href={`/evaluations/${runId}`}
          className="back-link"
        >
          <span>←</span>
          Back to result
        </Link>

        <div className="case-heading-meta">
          <div>
            <div className="overline">
              CASE {pairId}
            </div>

            <h1>
              What changed when additional context was available?
            </h1>
          </div>

          <span className="complete-badge">
            <span className="status-dot" />
            {item.passed ? "Verified" : "Requires review"}
          </span>
        </div>
      </section>

      <section className="change-summary">
        <div className="change-summary-label">
          WHAT CHANGED?
        </div>

        <h2>{changeSummary.title}</h2>

        <p>{changeSummary.description}</p>

        <div className="change-summary-facts">
          <div>
            <span>Interpretation</span>
            <strong>
              {item.base.interpretation_class ===
              item.variant.interpretation_class
                ? "No change"
                : "Changed"}
            </strong>
          </div>

          <div>
            <span>Support</span>
            <strong>
              {item.base.support_level ===
              item.variant.support_level
                ? "No change"
                : "Changed"}
            </strong>
          </div>

          <div>
            <span>Decision strength</span>
            <strong>
              {item.base.decision_strength ===
              item.variant.decision_strength
                ? "No change"
                : "Changed"}
            </strong>
          </div>
        </div>
      </section>

      <section className="context-comparison">
        <div className="comparison-card comparison-card-base">
          <div className="comparison-header">
            <div>
              <span className="comparison-eyebrow">
                WITHOUT ADDITIONAL CONTEXT
              </span>

              <h2>Original state</h2>
            </div>
          </div>

          <div className="comparison-main">
            <span className="comparison-label">
              What was understood
            </span>

            <h3>
              {interpretationSummary(
                item.base.interpretation_class,
              )}
            </h3>
          </div>

          <div className="comparison-detail">
            <span>Supporting information</span>

            <strong>
              {supportSummary(item.base.support_level)}
            </strong>
          </div>

          <div className="comparison-detail-row">
            <div>
              <span>Decision strength</span>

              <strong>
                {formatValue(
                  item.base.decision_strength,
                )}
              </strong>
            </div>

            <div>
              <span>Availability</span>

              <strong>
                {formatValue(item.base.availability)}
              </strong>
            </div>
          </div>

          <NotesList notes={item.base.notes} />

          <div className="evidence-block">
            <span>Evidence used</span>

            <EvidenceList
              snapshot={item.base}
              emptyMessage="This is the primary-only comparison state."
            />
          </div>
        </div>

        <div className="comparison-card comparison-card-context">
          <div className="comparison-header">
            <div>
              <span className="comparison-eyebrow">
                WITH ADDITIONAL CONTEXT
              </span>

              <h2>Context-aware state</h2>
            </div>
          </div>

          <div className="comparison-main">
            <span className="comparison-label">
              What was understood
            </span>

            <h3>
              {interpretationSummary(
                item.variant.interpretation_class,
              )}
            </h3>
          </div>

          <div className="comparison-detail">
            <span>Supporting information</span>

            <strong>
              {supportSummary(item.variant.support_level)}
            </strong>
          </div>

          <div className="comparison-detail-row">
            <div>
              <span>Decision strength</span>

              <strong>
                {formatValue(
                  item.variant.decision_strength,
                )}
              </strong>
            </div>

            <div>
              <span>Information timing</span>

              <strong>
                {formatValue(
                  item.variant.temporal_status,
                )}
              </strong>
            </div>
          </div>

          <NotesList notes={item.variant.notes} />

          <div className="evidence-block">
            <span>Evidence used in this state</span>

            <EvidenceList
              snapshot={item.variant}
              emptyMessage="No secondary evidence was used for this state."
            />
          </div>
        </div>
      </section>

      <section className="why-section">
        <div className="section-heading-row">
          <div>
            <div className="section-kicker">
              WHY THIS CASE PASSED
            </div>

            <h2>Checks behind the result.</h2>

            <p className="section-description">
              These checks describe how the controlled case was evaluated.
              They are separate from the business interpretation above.
            </p>
          </div>
        </div>

        <div className="validation-grid">
          {Object.entries(item.dimensions).map(
            ([name, passed]) => (
              <div
                className="validation-item validation-item-expanded"
                key={name}
              >
                <span
                  className={`validation-icon ${
                    passed
                      ? "passed"
                      : "failed"
                  }`}
                >
                  {passed ? "✓" : "!"}
                </span>

                <div>
                  <strong>
                    {checkLabel(name)}
                  </strong>

                  <span>
                    {passed
                      ? "Passed"
                      : "Requires review"}
                  </span>

                  <small>
                    {checkDescription(name)}
                  </small>
                </div>
              </div>
            ),
          )}
        </div>
      </section>

      <details className="technical-disclosure">
        <summary>
          <span>Technical details</span>

          <span className="technical-disclosure-icon">
            +
          </span>
        </summary>

        <div className="technical-disclosure-content">
          <div className="technical-explanation">
            <div className="section-kicker">
              FOR ADVANCED USERS
            </div>

            <h2>Evaluation details</h2>

            <p>
              These fields describe the underlying controlled
              experiment. They are kept here so the main result
              remains easy to understand.
            </p>
          </div>

          <div className="technical-grid">
            <div>
              <span>Case ID</span>
              <strong>{item.pair_id}</strong>
            </div>

            <div>
              <span>Evaluation split</span>
              <strong>{item.split}</strong>
            </div>

            <div>
              <span>Evidence valid</span>
              <strong>
                {item.variant.evidence_valid
                  ? "Yes"
                  : "No"}
              </strong>
            </div>

            <div>
              <span>Identity match</span>
              <strong>
                {formatValue(
                  item.variant.identity_match,
                )}
              </strong>
            </div>

            <div>
              <span>Reversion</span>
              <strong>
                {formatValue(
                  item.variant.reversion,
                )}
              </strong>
            </div>

            <div>
              <span>Recommended focus</span>
              <strong>
                {formatValue(
                  item.variant.recommended_focus,
                )}
              </strong>
            </div>
          </div>

          <div className="technical-check-explanations">
            {Object.entries(item.dimensions).map(
              ([name, passed]) => (
                <div
                  key={name}
                  className="technical-check"
                >
                  <strong>
                    {checkLabel(name)}
                  </strong>

                  <span>
                    {checkDescription(name)}
                  </span>

                  <em>
                    {passed ? "Passed" : "Requires review"}
                  </em>
                </div>
              ),
            )}
          </div>
        </div>
      </details>

      <div className="case-footer-action">
        <Link
          href={`/evaluations/${runId}`}
          className="button button-primary"
        >
          Back to all cases
          <span>→</span>
        </Link>
      </div>
    </main>
  );
}