from contextlib import contextmanager
import sqlite3
from ai_agent.config import system_prompt
from unittest.mock import patch
from ai_agent.utils import create_agent, DeterministicStubLLM, tools
from concurrent.futures import ThreadPoolExecutor
import threading
from ai_agent.sql_queries import get_asset_data

def test_agent_concurrent_status_update(db_agent_test, monkeypatch):

    barrier = threading.Barrier(2)

    # Keep the real implementation
    original_get_asset_data = get_asset_data

    def synchronised_get_asset_data(conn, asset_id):
        result = original_get_asset_data(conn, asset_id)

        print(
            threading.current_thread().name,
            "read:",
            result,
        )

        barrier.wait()

        return result

    monkeypatch.setattr(
        "ai_agent.tools.get_asset_data",
        synchronised_get_asset_data,
    )

    @contextmanager
    def test_db_conn():
        conn = sqlite3.connect(db_agent_test)
        conn.row_factory = sqlite3.Row

        try:
            yield conn
        finally:
            conn.close()

    def run_agent(prompt):
        llm = DeterministicStubLLM()
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
                        "content": prompt
                    }
                ]
            })

            return response

    def get_tool_messages(response):
        return [
            message
            for message in response["messages"]
            if message.type == "tool"
        ]

    with ThreadPoolExecutor(max_workers=2) as excutor:

        future_a = excutor.submit(
            run_agent,
            "Change asset Status DE10 Inactive", 
        )

        future_b = excutor.submit(
            run_agent,
            "Change asset Status DE10 Inactive", 
        )

        response_a = future_a.result()
        response_b = future_b.result()

        # print(response_a)
        # print(response_b)


        tool_messages_a = get_tool_messages(response_a)
        tool_messages_b = get_tool_messages(response_b)

        assert tool_messages_a
        assert tool_messages_b

        content_a = str(tool_messages_a[-1].content)
        content_b = str(tool_messages_b[-1].content)

        print("A:", content_a)
        print("B:", content_b)

        results = [
            "failure" if '"error": "CONCURRENT_UPDATE"' in content_a else "success",
            "failure" if '"error": "CONCURRENT_UPDATE"' in content_b else "success",
        ]

        assert sorted(results) == ['failure', 'success']


       