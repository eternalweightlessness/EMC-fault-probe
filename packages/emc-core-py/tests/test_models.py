from emc_core.tools.models import ToolCall, ToolResult, ToolSpec


def test_tool_spec_contains_model_facing_metadata() -> None:
    spec = ToolSpec(
        name="search_cases",
        description="查询 EMC 故障案例",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
            },
            "required": ["query"],
        },
    )

    assert spec.name == "search_cases"
    assert spec.description == "查询 EMC 故障案例"
    assert spec.parameters["required"] == ["query"]


def test_tool_call_stores_name_arguments_and_optional_call_id() -> None:
    call = ToolCall(
        name="search_cases",
        arguments={"query": "辐射发射超标"},
        call_id="call-001",
    )

    assert call.name == "search_cases"
    assert call.arguments["query"] == "辐射发射超标"
    assert call.call_id == "call-001"


def test_tool_result_stores_success_output() -> None:
    result = ToolResult(
        tool_name="search_cases",
        call_id="call-001",
        output="查询完成",
    )

    assert result.tool_name == "search_cases"
    assert result.call_id == "call-001"
    assert result.output == "查询完成"
    assert result.error is None
