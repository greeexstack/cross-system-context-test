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
      return "The additional information was considered, but it did not provide enough evidence to change the conclusion.";
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
      label: "More Information Needed",
      title:
        "We need more business detail before we can give you a clear conclusion.",
      description:
        "The information describes a general situation, but it does not yet identify a specific customer event, decision, or next step to evaluate.",
    };
  }

  if (result.interpretation_changed) {
    switch (result.variant.interpretation_class) {
      case "quote_followup_pending":
        return {
          kind: "changed",
          label: "Conclusion Changed",
          title:
            "Follow-up is now required.",
          description:
            "The latest information indicates that the quote or proposal needs follow-up.",
        };

      case "quote_pending_decision":
        return {
          kind: "changed",
          label: "Conclusion Changed",
          title:
            "The quote is still waiting for a decision.",
          description:
            "The latest information changed the business situation to a pending customer decision.",
        };

      case "negotiation_open":
        return {
          kind: "changed",
          label: "Conclusion Changed",
          title:
            "The customer discussion is still open.",
          description:
            "The latest information indicates that the customer conversation or negotiation remains active.",
        };

      case "service_completed_next_step_unrecorded":
        return {
          kind: "changed",
          label: "Conclusion Changed",
          title:
            "The service appears complete, but the next step is unclear.",
          description:
            "The latest information indicates that a follow-up action may still need to be recorded.",
        };

      default:
        return {
          kind: "changed",
          label: "Conclusion Changed",
          title:
            "The additional information changed the business conclusion.",
          description:
            "The new information points to a different business situation than the original information did.",
        };
    }
  }

  switch (result.variant.interpretation_class) {
    case "quote_pending_decision":
      return {
        kind: "preserved",
        label: "Conclusion Unchanged",
        title:
          "The follow-up decision remains unchanged.",
        description:
          "The quote is still waiting for a decision. The latest customer information was considered, but it does not indicate that a decision has been made. Follow-up is still required.",
      };

    case "quote_followup_pending":
      return {
        kind: "preserved",
        label: "Conclusion Unchanged",
        title:
          "Follow-up is still required.",
        description:
          "The additional information was considered, but the business situation still indicates that the quote or proposal needs follow-up.",
      };

    case "negotiation_open":
      return {
        kind: "preserved",
        label: "Conclusion Unchanged",
        title:
          "The customer discussion remains open.",
        description:
          "The additional information was considered, but it does not establish a different business situation.",
      };

    case "service_completed_next_step_unrecorded":
      return {
        kind: "preserved",
        label: "Conclusion Unchanged",
        title:
          "The service appears complete, but the next step is still unclear.",
        description:
          "The additional information was considered, but it does not establish a different next step.",
      };

    default:
      return {
        kind: "preserved",
        label: "No Material Change",
        title:
          "The additional information did not change the business conclusion.",
        description:
          "The new information was considered and did not establish a different business situation.",
      };
  }
}
function nextStepSummary(
  result: UserEvaluationResult,
) {
  switch (result.variant.interpretation_class) {
    case "quote_pending_decision":
      return {
        title:
          "Follow up with the customer about the pending quote decision.",
        description:
          "The quote is still awaiting a decision. The latest message shows the customer is ready to discuss the next step, so the next action is to continue that conversation and clarify the decision timeline.",
      };

    case "quote_followup_pending":
      return {
        title:
          "Follow up with the customer about the quote or proposal.",
        description:
          "The available information indicates that the quote or proposal still requires follow-up.",
      };

    case "negotiation_open":
      return {
        title:
          "Continue the customer discussion and confirm the next step.",
        description:
          "The customer discussion is still active, so the next action is to clarify what needs to happen next.",
      };

    case "service_completed_next_step_unrecorded":
      return {
        title:
          "Confirm and record the next step for the completed service.",
        description:
          "The service appears complete, but the next business action has not been clearly recorded.",
      };

    case "primary_state_uncertain":
      return {
        title:
          "Add the business event or decision you want to evaluate.",
        description:
          "Provide the specific customer event, decision, pending action, or next step that you want the evaluation to assess.",
      };

    default:
      return {
        title:
          "Review the result and decide the next business action.",
        description:
          "Use the conclusion together with the information considered to determine what should happen next.",
      };
  }
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
    Change
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
        How the business situation changed
      </h2>

      <p>
        This compares the original situation with the
        situation after the additional information was
        considered.
      </p>
    </div>
  </div>

  <div className="result-transition">
    <div className="result-state-card">
      <span>ORIGINAL CONCLUSION</span>

      <h3>
        {interpretationSummary(
          result.base.interpretation_class,
        )}
      </h3>
    </div>

    <div className="result-transition-arrow">
      →
    </div>

    <div className="result-state-card result-state-card-active">
      <span>AFTER THE NEW INFORMATION</span>

      <h3>
        {interpretationSummary(
          result.variant.interpretation_class,
        )}
      </h3>
    </div>
  </div>

  <div className="result-change-summary">
    {state.kind === "changed" && (
      <p>
        The additional information changed the business
        situation.
      </p>
    )}

    {state.kind === "preserved" && (
      <p>
        The additional information did not change the
        business situation.
      </p>
    )}

    {state.kind === "refined" && (
      <p>
        The business situation stayed the same after the
        additional information was considered.
      </p>
    )}

    {state.kind === "uncertain" && (
      <p>
        There is not enough information to establish a
        clear business situation.
      </p>
    )}
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

        <details className="result-information-details">
  <summary>
    <span>Information considered</span>
    <span
      className="result-information-chevron"
      aria-hidden="true"
    />
  </summary>

  <EvidenceList
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

  {(() => {
    const nextStep = nextStepSummary(result);

    return (
      <>
        <h2>
          {nextStep.title}
        </h2>

        <p>
          {nextStep.description}
        </p>
      </>
    );
  })()}

  <div className="result-action-row">
  <Link
    href={`/reports/${result.run_id}`}
    className="button button-primary"
  >
    View Report
    <span>→</span>
  </Link>

  <Link
    href="/evaluate"
    className="button button-ghost"
  >
    Run Another Evaluation
  </Link>
</div>
</section>


    </main>
  );
}