from dataclasses import dataclass

from experiment.analysis.context import CrossSystemContext
from experiment.diagnosis.cross_system import CrossSystemDiagnosis
from experiment.resolution.customer import CustomerMatch


@dataclass(frozen=True)
class CrossSystemAnalysis:
    opportunity_id: str
    primary_analysis: object
    context: CrossSystemContext
    customer_match: CustomerMatch | None
    diagnosis: CrossSystemDiagnosis