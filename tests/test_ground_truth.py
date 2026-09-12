from experiment.evaluation.ground_truth import GroundTruthLoader


def test_ground_truth_loader_loads_hidden_engagement():
    loader = GroundTruthLoader("scenarios")

    result = loader.load("hidden_engagement")

    assert result.scenario_id == "hidden_engagement"

    assert result.primary_only.finding is True
    assert result.primary_only.diagnosis_class == "internal_activity_gap"
    assert result.primary_only.confidence == "medium"
    assert result.primary_only.recommendation_class == "owner_followup"

    assert result.cross_system.finding is True
    assert result.cross_system.diagnosis_class == "internal_activity_gap"
    assert result.cross_system.confidence == "high"
    assert (
        result.cross_system.recommendation_class
        == "verify_communication_and_owner_followup"
    )

    assert result.incremental_information is True


def test_ground_truth_loader_loads_long_cycle():
    loader = GroundTruthLoader("scenarios")

    result = loader.load("long_cycle")

    assert result.scenario_id == "long_cycle"

    assert result.primary_only.finding is False
    assert result.primary_only.diagnosis_class == "no_finding"
    assert result.primary_only.confidence == "medium"
    assert result.primary_only.recommendation_class == "none"

    assert result.cross_system.finding is False
    assert result.cross_system.diagnosis_class == "no_finding"
    assert result.cross_system.confidence == "high"
    assert result.cross_system.recommendation_class == "none"

    assert result.incremental_information is False


def test_ground_truth_loader_loads_irrelevant_communication():
    loader = GroundTruthLoader("scenarios")

    result = loader.load("irrelevant_communication")

    assert result.scenario_id == "irrelevant_communication"

    assert result.primary_only.finding is True
    assert result.primary_only.diagnosis_class == "internal_activity_gap"
    assert result.primary_only.confidence == "medium"
    assert result.primary_only.recommendation_class == "owner_followup"

    assert result.cross_system.finding is True
    assert result.cross_system.diagnosis_class == "unrelated_communication"
    assert result.cross_system.confidence == "high"
    assert result.cross_system.recommendation_class == "owner_followup"

    assert result.incremental_information is False