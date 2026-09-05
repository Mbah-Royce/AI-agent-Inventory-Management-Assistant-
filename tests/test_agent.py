from ai_agent.utils import create_agent, DeterministicStubLLM, tools
from ai_agent.config import system_prompt
from unittest.mock import patch
import sqlite3
from contextlib import contextmanager

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

def test_agent_call_get_asset(db_agent_test):
    llm = DeterministicStubLLM()

    @contextmanager
    def test_db_conn():
        conn = sqlite3.connect(db_agent_test)
        conn.row_factory = sqlite3.Row

        try:
            yield conn
        finally:
            conn.close()

    with patch("ai_agent.tools.db_conn", test_db_conn):
        agent = create_agent(
            system_prompt=system_prompt, 
            tools=tools,
            model=llm
            )
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

        assert tools_calls[0]["name"] == "get_asset" 
        assert tools_calls[0]["args"]["asset_id"] == "EQ10"
        assert len(response["messages"]) > 0

        tool_message = next(
        message
        for message in messages
        if message.type == "tool"
)

        assert '"status"' in tool_message.content
        assert '"asset_id": "EQ10"' in tool_message.content

def test_agent_call_update_asset_status(db_agent_test):
    llm = DeterministicStubLLM()

    @contextmanager
    def test_db_conn():
        conn = sqlite3.connect(db_agent_test)
        conn.row_factory = sqlite3.Row

        try:
            yield conn
        finally:
            conn.close()

    with patch("ai_agent.tools.db_conn", test_db_conn):
        agent = create_agent(
            system_prompt=system_prompt, 
            tools=tools,
            model=llm
            )
        response = agent.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": "Change asset Status EQ10 Inactive",
                }
            ]
        })

        messages = response["messages"]

        tools_calls = []

        for message in messages:
            if getattr(message, "tool_calls", None):
                tools_calls.extend(message.tool_calls)

        assert tools_calls[0]["name"] == "change_asset_status" 
        assert tools_calls[0]["args"]["asset_id"] == "EQ10"
        assert tools_calls[0]["args"]["asset_status"] == "Inactive"
        assert len(response["messages"]) > 0

        tool_messages = [
        message
        for message in messages
        if message.type == "tool"
    ]

        assert tool_messages
        assert "EQ10" in tool_messages[0].content
        assert '"asset_id": "EQ10"' in tool_messages[0].content
        assert '"new_status": "Inactive"' in tool_messages[0].content
        assert '"new_version":' in tool_messages[0].content

def test_agent_call_update_asset_location(db_agent_test):
    llm = DeterministicStubLLM()

    @contextmanager
    def test_db_conn():
        conn = sqlite3.connect(db_agent_test)
        conn.row_factory = sqlite3.Row

        try:
            yield conn
        finally:
            conn.close()

    with patch("ai_agent.tools.db_conn", test_db_conn):
        agent = create_agent(
            system_prompt=system_prompt, 
            tools=tools,
            model=llm
            )
        response = agent.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": "Change asset location EQ10 to Manchester",
                }
            ]
        })

        messages = response["messages"]

        tools_calls = []

        for message in messages:
            if getattr(message, "tool_calls", None):
                tools_calls.extend(message.tool_calls)

        assert tools_calls[0]["name"] == "change_asset_location" 
        assert tools_calls[0]["args"]["asset_id"] == "EQ10"
        assert tools_calls[0]["args"]["asset_location"] == "Manchester"
        assert len(response["messages"]) > 0

        tool_messages = [
        message
        for message in messages
        if message.type == "tool"
    ]
        assert tool_messages
        assert "EQ10" in tool_messages[0].content
        assert '"asset_id": "EQ10"' in tool_messages[0].content
        assert '"new_location": "Manchester"' in tool_messages[0].content
        assert '"new_version":' in tool_messages[0].content

def test_agent_call_write_asset_fault_log(db_agent_test):
    llm = DeterministicStubLLM()

    @contextmanager
    def test_db_conn():
        conn = sqlite3.connect(db_agent_test)
        conn.row_factory = sqlite3.Row

        try:
            yield conn
        finally:
            conn.close()

    with patch("ai_agent.tools.db_conn", test_db_conn):
        agent = create_agent(
            system_prompt=system_prompt, 
            tools=tools,
            model=llm
            )
        response = agent.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": "Log fault of asset EQ10: low power output",
                }
            ]
        })

        messages = response["messages"]

        tools_calls = []

        for message in messages:
            if getattr(message, "tool_calls", None):
                tools_calls.extend(message.tool_calls)

        assert tools_calls[0]["name"] == "write_asset_fault_log" 
        assert tools_calls[0]["args"]["asset_id"] == "EQ10"
        assert tools_calls[0]["args"]["asset_fault"] == "low power output"
        assert len(response["messages"]) > 0

        tool_messages = [
        message
        for message in messages
        if message.type == "tool"
    ]
        assert tool_messages
        assert "EQ10" in tool_messages[0].content
        assert '"asset_id": "EQ10"' in tool_messages[0].content
        assert '"fault": "low power output"' in tool_messages[0].content
