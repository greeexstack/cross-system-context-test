
from experiment.analysis.context import (
    CommunicationSourceStatus,
    CrossSystemContext,
    CustomerIdentityStatus,
)
from experiment.analysis.cross_system import CrossSystemAnalysis
from experiment.analysis.runner import PrimaryOnlyAnalysisRunner
from experiment.diagnosis.cross_system import CrossSystemDiagnoser
from experiment.domain.models import Communication, Opportunity
from experiment.resolution.customer import CustomerResolver


class CrossSystemAnalysisRunner:
    def __init__(
        self,
        primary_runner: PrimaryOnlyAnalysisRunner | None = None,
        diagnoser: CrossSystemDiagnoser | None = None,
        resolver: CustomerResolver | None = None,
    ):
        self.primary_runner = primary_runner or PrimaryOnlyAnalysisRunner()
        self.diagnoser = diagnoser or CrossSystemDiagnoser()
        self.resolver = resolver or CustomerResolver()

    def run(
        self,
        opportunity: Opportunity,
        crm_customer,
        evaluation_at,
        communication: Communication | None,
        communication_source_status: CommunicationSourceStatus | None = None,
    ) -> CrossSystemAnalysis:
        primary_analysis = self.primary_runner.run(
            opportunity,
            evaluation_at,
        )

        if communication_source_status is None:
            if communication is None:
                communication_source_status = (
                    CommunicationSourceStatus.UNAVAILABLE
                )
            else:
                communication_source_status = (
                    CommunicationSourceStatus.COMMUNICATION_OBSERVED
                )

        customer_match = self._resolve_customer(
            crm_customer,
            communication,
        )

        if customer_match is None:
            if (
                communication_source_status
                == CommunicationSourceStatus.UNAVAILABLE
            ):
                customer_identity_status = CustomerIdentityStatus.UNAVAILABLE
            else:
                customer_identity_status = CustomerIdentityStatus.NOT_OBSERVED

        elif customer_match.status == "confident_match":
            customer_identity_status = CustomerIdentityStatus.CONFIDENT_MATCH

        elif customer_match.status == "ambiguous_match":
            customer_identity_status = CustomerIdentityStatus.AMBIGUOUS_MATCH

        else:
            customer_identity_status = CustomerIdentityStatus.NO_MATCH

        usable_communication = self._usable_communication(
            communication,
            customer_match,
        )

        diagnosis = self.diagnoser.diagnose(
            opportunity,
            usable_communication,
            primary_analysis.diagnosis.evidence,
            primary_analysis.baseline,
            primary_analysis.detection,
            customer_identity_status,
            communication_source_status,
        )

        context = CrossSystemContext(
            communication_source_status=communication_source_status,
            customer_identity_status=customer_identity_status,
        )

        return CrossSystemAnalysis(
            opportunity_id=opportunity.id,
            primary_analysis=primary_analysis,
            context=context,
            customer_match=customer_match,
            diagnosis=diagnosis,
        )

    def _resolve_customer(
        self,
        crm_customer,
        communication: Communication | None,
    ):
        if communication is None:
            return None

        communication_customer = {
            "id": communication.customer_id,
            "name": communication.customer_name,
            "email": communication.customer_email,
            "phone": communication.customer_phone,
        }

        return self.resolver.resolve(
            crm_customer,
            communication_customer,
        )

    @staticmethod
    def _usable_communication(
        communication: Communication | None,
        customer_match,
    ) -> Communication | None:
        if communication is None:
            return None

        if customer_match is None:
            return None

        if customer_match.status != "confident_match":
            return None

        return communication
