from ai_agent.utils import create_agent, DeterministicStubLLM
from ai_agent.config import system_prompt

def test_agent_returns_response():
    llm = DeterministicStubLLM()
    agent = create_agent(system_prompt=system_prompt, model=llm)
    response = agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": "Hello",
            }
        ]
    })

    assert response is not None
    assert "messages" in response
    assert len(response["messages"]) > 0

def test_agent_calls_get_asset():
    llm = DeterministicStubLLM()
    agent = create_agent(system_prompt=system_prompt, model=llm)
    response = agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": "Get asset EQ10 info",
            }
        ]
    })

    messages = response["messages"]

    tools_calls = []

    for message in messages:
        if getattr(message, "tool_calls", None):
            tools_calls.extend(message.tool_calls)

    print(response)
    assert tools_calls[0]["name"] == "get_assets" 
    assert tools_calls[0]["args"]["asset_id"] == "EQ10"
    assert len(response["messages"]) > 0

# def test_agent_calls_change_asset_status():
    # llm = DeterministicStubLLM()
    # agent = create_agent(system_prompt=system_prompt, model=llm)
    # response = agent.invoke({
    #     "messages": [
    #         {
    #             "role": "user",
    #             "content": "Get asset EQ10 info",
    #         }
    #     ]
    # })

    # messages = response["messages"]

    # tools_calls = []
    # print(response)
    # for message in messages:
    #     if getattr(message, "tool_calls", None):
    #         tools_calls.extend(message.tool_calls)

    # print(tools_calls)
    # assert tools_calls[0]["name"] == "change_asset_status" 
    # assert tools_calls[0]["args"]["asset_id"] == "EQ10"
    # assert len(response["messages"]) > 0