"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  getUserEvaluation,
  type UserEvaluationResult,
} from "@/lib/api";
import {
  getResultState,
  interpretationSummary,
  nextStepSummary,
} from "@/lib/userEvaluationResult";

function formatValue(value: string | null) {
  if (!value) {
    return "Not specified";
  }

  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatSentence(value: string | null) {
  if (!value) {
    return "";
  }

  const sentence = value.trim().replace(/\s+/g, " ");

  return (
    sentence.charAt(0).toUpperCase() +
    sentence.slice(1)
  );
}

function statusLabel(value: string | null) {
  switch (value) {
    case "confident_match":
      return "Confirmed match";

    case "ambiguous_match":
      return "Ambiguous match";

    case "no_match":
      return "No match";

    case "fresh":
      return "Current";

    case "clearly_stale":
      return "Too old to treat as current";

    case "available":
      return "Available";

    case "unavailable":
      return "Unavailable";

    default:
      return formatValue(value);
  }
}



export default function UserEvaluationReportPage({
  params,
}: {
  params: Promise<{ run_id: string }>;
}) {
  const [result, setResult] =
    useState<UserEvaluationResult | null>(null);

  const [error, setError] = useState("");

  useEffect(() => {
    params.then(({ run_id }) => {
      getUserEvaluation(run_id)
        .then(setResult)
        .catch((err) => {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load this report.",
          );
        });
    });
  }, [params]);

  const state = useMemo(() => {
    if (!result) {
      return null;
    }

    return getResultState(result);
  }, [result]);

  const nextStep = useMemo(() => {
    if (!result) {
      return null;
    }

    return nextStepSummary(result);
  }, [result]);

  if (error) {
    return (
      <main className="site-shell report-page">
        <section className="empty-state">
          <div className="section-kicker">
            REPORT UNAVAILABLE
          </div>

          <h1>We could not load this report.</h1>

          <p>{error}</p>

          <Link
            href="/evaluate"
            className="button button-primary"
          >
            Start another evaluation
          </Link>
        </section>
      </main>
    );
  }

  if (!result || !state || !nextStep) {
    return (
      <main className="site-shell report-page">
        <section className="loading-state">
          <div className="loader-ring" />
          <span>Loading report...</span>
        </section>
      </main>
    );
  }

  return (
    <main className="site-shell report-page">
      <nav className="nav report-screen-only">
        <Link href="/" className="logo">
          <span className="logo-mark">C</span>

          <span className="logo-name">
            Cross-System Context
          </span>
        </Link>

        <div className="nav-links">
          <Link href="/">
            Overview
          </Link>

          <Link href="/evaluate">
            Evaluations
          </Link>

          <Link href="/integrate">
            Integrations
          </Link>

          <Link href="/reports" className="nav-active">
            Reports
          </Link>
        </div>
      </nav>

      <div className="report-toolbar">
  <Link href={`/user-evaluations/${result.run_id}`} className="back-link">
    ← Back to result
  </Link>
</div>

      <header className="report-header">

        <h1>{result.name}</h1>

        <p className="report-purpose">
          {formatSentence(result.objective)}
        </p>


      </header>

            <section
        className={`report-conclusion report-conclusion-${state.kind}`}
      >
        <div className="section-kicker">
          {state.kind === "uncertain"
            ? "NEEDS MORE INFORMATION"
            : "YOUR RESULT"}
        </div>

        <h2>{state.title}</h2>

        <p>{state.description}</p>
      </section>

      <section className="report-section">
        <div className="section-kicker">
          WHAT YOU TOLD US
        </div>

        <h2>Current situation and new information</h2>

        <div className="report-context-grid">
          <div className="report-context-card">
            <span>Current situation</span>

            <p>
              {formatSentence(
                result.primary_context,
              )}
            </p>
          </div>

          <div className="report-context-card">
            <span>New information</span>

            <p>
              {formatSentence(
                result.additional_context,
              )}
            </p>
          </div>
        </div>
      </section>

                        {state.kind === "uncertain" ? (
        <section className="report-section report-needs">
          <div className="report-section-heading">
            <h2>What we need</h2>
          </div>

          <div className="report-needs-intro">
            <h3>Give us one specific customer situation.</h3>

<p>
  We need one specific customer event, decision, or pending
  action to evaluate.
</p>
          </div>

          <div className="report-example-list">
            <div className="report-example">
              <span>01</span>

              <div>
                <strong>A quote is waiting for a response.</strong>
                <p>
                  Tell us what the customer said or what decision is pending.
                </p>
              </div>
            </div>

            <div className="report-example">
              <span>02</span>

              <div>
                <strong>A customer asked for more time.</strong>
                <p>
                  Tell us what they said and what happens next.
                </p>
              </div>
            </div>

            <div className="report-example">
              <span>03</span>

              <div>
                <strong>A customer is ready for the next step.</strong>
                <p>
                  Tell us what action or decision is now expected.
                </p>
              </div>
            </div>
          </div>
        </section>
      ) : (
        <section className="report-section">
          <div className="report-section-heading">
            <span className="report-section-number">01</span>
            <h2>What changed</h2>
          </div>

          <p className="report-section-intro">
            Here is how the conclusion changed after the new information
            was considered.
          </p>

          <div className="report-transition">
            <div className="report-transition-card">
              <span>Before</span>

              <strong>
                {interpretationSummary(
                  result.base.interpretation_class,
                )}
              </strong>
            </div>

            <div className="report-transition-arrow">
              →
            </div>

            <div className="report-transition-card active">
              <span>After</span>

              <strong>
                {interpretationSummary(
                  result.variant.interpretation_class,
                )}
              </strong>
            </div>
          </div>
        </section>
      )}

<section className="report-section">
  <div className="report-section-heading">
    <span className="report-section-number">02</span>
    <h2>What the evaluation considered</h2>
  </div>

  <p className="report-section-intro">
    This is the information available when the evaluation was run
    and the checks applied before reaching the result.
  </p>

  <div className="report-context-grid">
    <div className="report-context-card">
      <span>Identity</span>
      <p>{statusLabel(result.variant.identity_match)}</p>
    </div>

    <div className="report-context-card">
      <span>Timing</span>
      <p>{statusLabel(result.variant.temporal_status)}</p>
    </div>

    <div className="report-context-card">
      <span>Availability</span>
      <p>{statusLabel(result.variant.availability)}</p>
    </div>

    <div className="report-context-card">
      <span>Evidence validity</span>
      <p>
        {result.variant.evidence_valid
          ? "Valid evidence was available."
          : "Evidence requires review."}
      </p>
    </div>
  </div>

  <div className="report-section-heading" style={{ marginTop: 28 }}>
    <h2>Information used</h2>
  </div>

  {result.variant.evidence.length === 0 ? (
    <div className="result-empty">
      No additional information was used for this conclusion.
    </div>
  ) : (
    <div className="result-evidence-list">
      {result.variant.evidence.map((evidence) => (
        <article
          key={evidence.evidence_id}
          className="result-evidence"
        >
          <div className="result-evidence-head">
            <div>
              <span>Information used</span>
              <strong>{evidence.subject}</strong>
            </div>

            <small>
              {evidence.direction === "inbound"
                ? "Incoming"
                : "Provided"}{" "}
              · {formatValue(evidence.channel)}
            </small>
          </div>

          <p>{evidence.summary}</p>

          <time>
            {new Date(evidence.occurred_at).toLocaleString()}
          </time>
        </article>
      ))}
    </div>
  )}

  {result.variant.notes.length > 0 ? (
    <div className="result-notes">
      {result.variant.notes.map((note, index) => (
        <p key={`${note}-${index}`}>{note}</p>
      ))}
    </div>
  ) : null}
</section>
      <section className="report-next-step">
        <div className="section-kicker">
  WHAT TO DO NEXT
</div>
        <h2>{nextStep.title}</h2>

        <p>{nextStep.description}</p>
      </section>
             <div className="report-actions">
        <button
          type="button"
          className="button button-ghost"
          onClick={() => window.print()}
        >
          Print / Save as PDF
        </button>

        <Link
          href="/evaluate"
          className="button button-primary"
        >
          Run Another Evaluation
          <span>→</span>
        </Link>
      </div>

<div className="report-library-link">
  <Link href="/reports">
    View all reports
    <span aria-hidden="true">→</span>
  </Link>
</div>
            <footer className="report-footer">
        <span>
          Report ID: {result.run_id}
        </span>

        <span>
          Created:{" "}
          {new Date(result.created_at).toLocaleString()}
        </span>
      </footer>
    </main>
  );
}