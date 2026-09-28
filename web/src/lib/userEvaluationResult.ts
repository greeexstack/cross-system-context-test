import type {
  UserEvaluationResult,
} from "@/lib/api";

export type ResultState = {
  kind: "changed" | "refined" | "preserved" | "uncertain";
  label: string;
  title: string;
  description: string;
};

export function interpretationSummary(
  value: string | null,
) {
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
      return value
        ? value
            .replaceAll("_", " ")
            .replace(/\b\w/g, (letter) => letter.toUpperCase())
        : "Not specified";
  }
}

export function getResultState(
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

export function nextStepSummary(
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
