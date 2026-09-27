"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  getUserEvaluation,
  type ReasoningSnapshot,
  type UserEvaluationResult,
} from "@/lib/api";

type ResultState = {
  kind: "changed" | "refined" | "preserved" | "uncertain";
  label: string;
  title: string;
  description: string;
};

function formatValue(value: string | null) {
  if (!value) {
    return "Not specified";
  }

  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatUserTitle(value: string | null) {
  if (!value) {
    return "";
  }

  const cleaned = value.trim().replace(/\s+/g, " ");

  return cleaned
    .replace(/\bfollow\s*[- ]?\s*up\b/gi, "Follow-up")
    .replace(/\bdecision\b/gi, "Decision")
    .replace(/\bproposal\b/gi, "Proposal")
    .replace(/\bquote\b/gi, "Quote")
    .replace(/\border\b/gi, "Order")
    .replace(/\bservice\b/gi, "Service")
    .replace(/\bcustomer\b/gi, "Customer")
    .replace(/\s+/g, " ")
    .replace(/^./, (letter) => letter.toUpperCase());
}

function formatUserSentence(value: string | null) {
  if (!value) {
    return "";
  }

  let sentence = value.trim().replace(/\s+/g, " ");

  sentence = sentence
    .replace(/\bfollow\s*[- ]?\s*up\b/gi, "follow-up")
    .replace(
      /\bhow i can make my system more efficient to convert leads\b/i,
      "How can I make my system more efficient at converting leads",
    );

  sentence =
    sentence.charAt(0).toUpperCase() + sentence.slice(1);

  if (!/[.!?]$/.test(sentence)) {
    sentence += ".";
  }

  return sentence;
}

function interpretationSummary(value: string | null) {
  switch (value) {
    case "quote_pending_decision":
      return "The quote or proposal is still waiting for a decision.";

    case "quote_followup_pending":
      return "The quote or proposal needs follow-up.";

    case "negotiation_open":
      return "The customer discussion is still open.";

    case "service_completed_next_step_unrecorded":
      return "The service appears complete, but the next step is not clear.";

    case "primary_state_uncertain":
      return "There is not enough information to identify a clear business situation.";

    default:
      return formatValue(value);
  }
}

function supportSummary(value: string | null) {
  switch (value) {
    case "no_secondary_evidence":
      return "No additional information was available.";

    case "primary_only":
      return "The conclusion is based only on the original information.";

    case "secondary_supported":
      return "The additional information strengthened the existing conclusion.";

    case "supported_by_secondary_context":
      return "The additional information supports the existing conclusion.";

    case "weakened_by_secondary_context":
      return "The additional information made the existing conclusion less certain.";

    case "temporal_context_rejected":
      return "The information was too old to treat as current.";

    case "safe_fallback_primary_only":
      return "The supporting source was unavailable, so the original conclusion was kept.";

    default:
      return formatValue(value);
  }
}

function signalSummary(value: string | null) {
  switch (value) {
    case "high":
      return "Strong support";

    case "moderate":
      return "Moderate support";

    case "weak":
      return "Limited support";

    case "low":
      return "Limited support";

    default:
      return "Not enough information";
  }
}

function getResultState(
  result: UserEvaluationResult,
): ResultState {
  const uncertain =
    result.base.interpretation_class ===
      "primary_state_uncertain" &&
    result.variant.interpretation_class ===
      "primary_state_uncertain";

  if (uncertain) {
    return {
      kind: "uncertain",
      label: "MORE INFORMATION NEEDED",
      title:
        "There is not enough information to make a clear business conclusion.",
      description:
        "The information describes a situation, but it does not yet identify a specific customer event, business decision, or next step that the evaluation can assess.",
    };
  }

  if (result.interpretation_changed) {
    return {
      kind: "changed",
      label: "ADDITIONAL SUPPORT FOUND",
      title:
        "The additional information changed the conclusion.",
      description:
        "The new information points to a different business situation than the original information did.",
    };
  }

  if (
    result.support_changed ||
    result.decision_strength_changed
  ) {
    return {
      kind: "refined",
      label: "CONCLUSION STRENGTHENED",
      title:
        "The conclusion stayed the same, but the new information added useful support.",
      description:
        "The additional information did not change the main situation, but it changed how strongly that conclusion is supported.",
    };
  }

  return {
    kind: "preserved",
    label: "NO MATERIAL CHANGE",
    title:
      "The additional information did not materially change the conclusion.",
    description:
      "The result remained aligned with what the original information indicated.",
  };
}

function EvidenceList({
  snapshot,
}: {
  snapshot: ReasoningSnapshot;
}) {
  if (snapshot.evidence.length === 0) {
    return (
      <div className="result-empty">
        No additional information was used for this conclusion.
      </div>
    );
  }

  return (
    <div className="result-evidence-list">
      {snapshot.evidence.map((evidence) => (
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
              • {formatValue(evidence.channel)}
            </small>
          </div>

          <p>{evidence.summary}</p>

          <time>
            {new Date(
              evidence.occurred_at,
            ).toLocaleString()}
          </time>
        </article>
      ))}
    </div>
  );
}

function Notes({
  snapshot,
}: {
  snapshot: ReasoningSnapshot;
}) {
  if (snapshot.notes.length === 0) {
    return null;
  }

  return (
    <div className="result-notes">
      {snapshot.notes.map((note, index) => (
        <p key={`${note}-${index}`}>
          {note}
        </p>
      ))}
    </div>
  );
}

export default function UserEvaluationResultPage({
  params,
}: {
  params: Promise<{ run_id: string }>;
}) {
  const [result, setResult] =
  useState<UserEvaluationResult | null>(null);

const [error, setError] = useState("");

const [activeSection, setActiveSection] =
  useState("summary");

  useEffect(() => {
    params.then(({ run_id }) => {
      getUserEvaluation(run_id)
        .then(setResult)
        .catch((err) => {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load this evaluation.",
          );
        });
    });
  }, [params]);
  useEffect(() => {
  const sectionIds = [
    "summary",
    "change",
    "why",
    "information",
    "next-step",
  ];

  const sections = sectionIds
    .map((id) => document.getElementById(id))
    .filter(
      (section): section is HTMLElement =>
        section !== null,
    );

  if (sections.length === 0) {
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort(
          (a, b) =>
            b.intersectionRatio -
            a.intersectionRatio,
        );

      if (visible.length > 0) {
        setActiveSection(visible[0].target.id);
      }
    },
    {
      rootMargin: "-20% 0px -65% 0px",
      threshold: [0.1, 0.3, 0.6],
    },
  );

  sections.forEach((section) =>
    observer.observe(section),
  );

  return () => observer.disconnect();
}, [result]);

  const state = useMemo(() => {
    if (!result) {
      return null;
    }

    return getResultState(result);
  }, [result]);

  if (error) {
    return (
      <main className="site-shell">
        <section className="empty-state">
          <div className="section-kicker">
            RESULT UNAVAILABLE
          </div>

          <h1>
            We could not load this evaluation.
          </h1>

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

  if (!result || !state) {
    return (
      <main className="site-shell">
        <section className="loading-state">
          <div className="loader-ring" />
          <span>Loading evaluation...</span>
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
          <Link href="/evaluate">
            Evaluations
          </Link>

          <Link href="/integrate">
            Integrate
          </Link>
        </div>
      </nav>

      <section className="result-page-header">
        <Link
          href="/evaluate"
          className="back-link"
        >
          ← New evaluation
        </Link>

        <div className="section-kicker">
          EVALUATION RESULT
        </div>

        <h1>
          {formatUserTitle(result.name)}
        </h1>

        <div className="result-user-goal">
          <span>Your goal</span>

          <blockquote>
            “{formatUserSentence(result.objective)}”
          </blockquote>
        </div>
        <div className="result-user-context">
  <div className="result-user-context-header">
    <span>What you shared</span>
  </div>

  <div className="result-user-context-grid">
    <div>
      <span>Current situation</span>

      <p>
        {formatUserSentence(
          result.primary_context,
        )}
      </p>
    </div>

    <div>
      <span>Additional information</span>

      <p>
        {formatUserSentence(
          result.additional_context,
        )}
      </p>
    </div>
  </div>
</div>
      </section>

      <nav
        className="result-local-nav"
        aria-label="Result sections"
      >
        <span className="result-local-nav-label">
          On this page
        </span>

        <a
  href="#summary"
  className={
    activeSection === "summary"
      ? "active"
      : ""
  }
>
  Summary
</a>

<a
  href="#change"
  className={
    activeSection === "change"
      ? "active"
      : ""
  }
>
  What changed
</a>

<a
  href="#why"
  className={
    activeSection === "why"
      ? "active"
      : ""
  }
>
  Why this result
</a>

<a
  href="#information"
  className={
    activeSection === "information"
      ? "active"
      : ""
  }
>
  Information used
</a>

<a
  href="#next-step"
  className={
    activeSection === "next-step"
      ? "active"
      : ""
  }
>
  Next step
</a>
      </nav>

      <section
        id="summary"
        className={`result-answer result-answer-${state.kind}`}
      >
        <div className="result-answer-label">
          {state.label}
        </div>

        <h2>{state.title}</h2>

        <p>{state.description}</p>
      </section>

      <section
        id="change"
        className="result-section result-section-tight"
      >
        <div className="result-section-heading">
          <div>
            <div className="section-kicker">
              WHAT CHANGED
            </div>

            <h2>
              Before and after the new information
            </h2>

            <p>
              This shows whether the information you
              added changed the conclusion.
            </p>
          </div>
        </div>

        <div className="result-transition">
          <div className="result-state-card">
            <span>ORIGINAL INFORMATION</span>

            <h3>
              {interpretationSummary(
                result.base.interpretation_class,
              )}
            </h3>

            <p>
              {supportSummary(
                result.base.support_level,
              )}
            </p>

            <small>
              {signalSummary(
                result.base.decision_strength,
              )}
            </small>
          </div>

          <div className="result-transition-arrow">
            →
          </div>

          <div className="result-state-card result-state-card-active">
            <span>WITH ADDITIONAL INFORMATION</span>

            <h3>
              {interpretationSummary(
                result.variant.interpretation_class,
              )}
            </h3>

            <p>
              {supportSummary(
                result.variant.support_level,
              )}
            </p>

            <small>
              {signalSummary(
                result.variant.decision_strength,
              )}
            </small>
          </div>
        </div>
      </section>

      <section
        id="why"
        className="result-section"
      >
        <div className="result-section-heading">
          <div>
            <div className="section-kicker">
              WHY
            </div>

            <h2>
              Why this is the result
            </h2>

            <p>
              The evaluation explains what the new
              information did to the original conclusion.
            </p>
          </div>
        </div>

        <div className="result-input-grid">
          <article>
            <span>
              Original information
            </span>

            <p>
              {supportSummary(
                result.base.support_level,
              )}
            </p>
          </article>

          <article>
            <span>
              New information
            </span>

            <p>
              {supportSummary(
                result.variant.support_level,
              )}
            </p>
          </article>
        </div>
      </section>

      <section
        id="information"
        className="result-section"
      >
        <div className="result-section-heading">
          <div>
            <div className="section-kicker">
              INFORMATION USED
            </div>

            <h2>
              What the evaluation considered
            </h2>

            <p>
              This is the information available when
              the evaluation was run.
            </p>
          </div>
        </div>

        <details>
          <summary>
            Show information used
          </summary>

          <EvidenceList
            snapshot={result.variant}
          />

          <Notes
            snapshot={result.variant}
          />
        </details>
      </section>



      <section
        id="next-step"
        className="result-next-step"
      >
        <div className="section-kicker">
          NEXT STEP
        </div>

        {state.kind === "uncertain" ? (
          <>
            <h2>
              Add the business event or decision
              you want to evaluate.
            </h2>

            <p>
              Useful details include what happened
              with the customer, what the customer did,
              what is currently waiting, what decision
              is pending, or what next step was agreed.
            </p>
          </>
        ) : (
          <>
            <h2>
              Use this result as the starting point
              for the next business action.
            </h2>

            <p>
              Review the conclusion alongside the
              information shown above and decide what
              should happen next in your workflow.
            </p>
          </>
        )}

        <Link
          href="/evaluate"
          className="button button-primary"
        >
          Run another evaluation
          <span>→</span>
        </Link>
      </section>


    </main>
  );
}