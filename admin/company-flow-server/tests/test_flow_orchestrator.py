from company_flow_server.contracts.models import CrewRunResult
from company_flow_server.server.flow_models import FlowDefinition, FlowStep
from company_flow_server.server.orchestrator import FlowOrchestrator


class FakeExecutor:
    def run(self, crew_id, version, inputs, **kwargs):
        if crew_id == "a":
            return CrewRunResult(outputs={"value": inputs["value"] + "-a"})
        return CrewRunResult(outputs={"value": inputs["value"] + "-b"})


def test_flow_resolves_previous_step_outputs():
    flow = FlowDefinition(
        flow_id="f",
        version="1",
        name="f",
        steps=(
            FlowStep("s1", "a", "1", {"value": "$flow.input"}),
            FlowStep("s2", "b", "1", {"value": "$steps.s1.outputs.value"}),
        ),
        output={"result": "$steps.s2.outputs.value"},
    )
    result = FlowOrchestrator(FakeExecutor()).run(flow, {"input": "x"})
    assert result.outputs == {"result": "x-a-b"}
