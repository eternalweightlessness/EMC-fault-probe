from emc_runtime_local.parser import parse_prompt_tool_call


def test_prompt_parser_uses_last_valid_tool_call_object() -> None:
    reply = (
        '思考 {"name":"wrong","arguments":{}} '
        '最终 {"name":"search_cases","arguments":{"query":"辐射发射"}}'
    )

    call = parse_prompt_tool_call(reply)

    assert call is not None
    assert call.name == "search_cases"
    assert call.arguments == {"query": "辐射发射"}
    assert call.call_id is not None


def test_prompt_parser_returns_none_for_normal_answer() -> None:
    assert parse_prompt_tool_call("这是普通回答。") is None
