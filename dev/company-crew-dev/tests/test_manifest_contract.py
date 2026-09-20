from company_crew_sdk.contracts import validate_contract


def test_contract_required_and_type():
    schema = {
        "required": ["incident_id"],
        "properties": {"incident_id": {"type": "string"}},
    }
    validate_contract({"incident_id": "INC-1"}, schema, label="inputs")
