import random
import sqlite3
import os
import time

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, SystemMessage, BaseMessage, ToolMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.language_models.chat_models import BaseChatModel
from langchain.agents import create_agent
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from typing import Any, List, Optional, Sequence
from tools import (change_asset_location, change_asset_status, log_asset_fault, get_asset_fault_history,
                   get_asset_info_with_logs)


# ================================
# DATABASE SETUP
# ================================
def init_db():
    # sqlite db setup
    conn = sqlite3.connect(os.getenv('DB_NAME'))
    try:
        cursor = conn.cursor()

        cursor.execute('DROP TABLE IF EXISTS ASSETS')
        cursor.execute('DROP TABLE IF EXISTS ASSET_FAULT_LOGS')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ASSETS(
                asset_id TEXT PRIMARY KEY,
                type TEXT UNIQUE NOT NULL CHECK(type IN('Equipment','Vehicle','Device')),
                location TEXT NOT NULL,
                status TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ASSET_FAULT_LOGS(
                assets_fault_log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                fault TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                asset_id INTEGER,
                FOREIGN KEY (asset_id) REFERENCES ASSETS (asset_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS idempotency_keys(
                idempotency_key TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                response TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_operations(
                operation_id TEXT PRIMARY KEY,
                idempotency_key TEXT UNIQUE NOT NULL,
                operation_type TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                status TEXT NOT NULL
            )        
        ''')

        cursor.execute("INSERT OR IGNORE INTO ASSETS (asset_id,type,location,status) "
                       "values ('EQ10','Equipment','warehouse_main','Expired')")
        cursor.execute("INSERT OR IGNORE INTO ASSETS (asset_id,type,location,status) "
                       "values ('DE10','Device','warehouse_main','quarantine')")
        cursor.execute("INSERT OR IGNORE INTO ASSETS (asset_id,type,location,status) "
                       "values ('VE10','Vehicle','warehouse_main','flAT')")

        cursor.execute("INSERT OR IGNORE INTO ASSET_FAULT_LOGS (asset_id,fault) "
                       "values ('EQ10', 'jammed motor')")
        cursor.execute("INSERT OR IGNORE INTO ASSET_FAULT_LOGS (asset_id,fault) "
                       "values ('DE10','broken screw')")
        cursor.execute("INSERT OR IGNORE INTO ASSET_FAULT_LOGS (asset_id,fault) "
                       "values ('VE10','low battery')")

        conn.commit()
    except Exception:
        raise
    finally:
        conn.close()


def db_conn():
    return sqlite3.connect(os.getenv('DB_NAME'))


# ================================
# STUB LLM SETUP
# ================================

class DeterministicStubLLM(BaseChatModel):

    @property
    def _llm_type(self) -> str:
        return "deterministic-stub"

    def bind_tools(
        self,
        tools: Sequence[Any],
        **kwargs: Any,
    ):
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:

        print("\n--- STUB RECEIVED ---")

        for message in messages:
            print(
                type(message).__name__,
                ":",
                message.content,
            )

        if any(
            isinstance(message, ToolMessage)
            for message in messages
        ):
            response = AIMessage(
                content="Asset EQ10 status was changed successfully."
            )

            return ChatResult(
                generations=[
                    ChatGeneration(message=response)
                ]
            )

        # Get user text
        prompt = "\n".join(
            str(message.content)
            for message in messages
        ).lower()

        # Deterministic decision
        if "eq10" in prompt and "destroyed" in prompt:

            response = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "change_asset_status",
                        "args": {
                            "asset_id": "EQ10",
                            "asset_status": "des",
                        },
                        "id": "stub-change-status-eq10",
                    }
                ],
            )
        if "eq10 " in prompt and "location" in prompt:

            response = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "change_asset_location",
                        "args": {
                            "asset_id": "EQ10",
                            "asset_location": "Manchester",
                        },
                        "id": "stub-change-location-eq10",
                    }
                ],
            )
        if "eq10 " in prompt and "fault" in prompt:

            response = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "log_asset_fault",
                        "args": {
                            "asset_id": "EQ10",
                            "asset_fault": "low power",
                        },
                        "id": "stub-change-location-eq10",
                    }
                ],
            )

        else:
            response = AIMessage(
                content="STUB: No matching action."
            )

        return ChatResult(
            generations=[
                ChatGeneration(
                    message=response
                )
            ]
        )
# ================================
# LLM SETUP
# ================================
def get_llm() -> BaseChatModel | str:
    if os.getenv('USE_STUB').lower() == 'true':
        print("Using Deterministic LLM")
        return DeterministicStubLLM()
    try:
        print("Using local model")
        llm = ChatOllama(model="llama3", timeout=2, temperature=0)
        llm.invoke("ping")

        print("Using local model")
        return llm
    except Exception as e:
        print(f"Local model unavailable: {e}")
        print("Local model not found. Falling back to stub")
        return DeterministicStubLLM()


# ================================
# AGENT SETUP
# ================================
def agent_create(system_prompt):
    # prompt = ChatPromptTemplate.from_messages([
    #     ("system", system_prompt),
    #     MessagesPlaceholder(variable_name="chat_history"),
    #     ("human", "{input}"),
    #     MessagesPlaceholder(variable_name="agent_scratchpad"),
    # ])

    tools = [change_asset_status, change_asset_location, log_asset_fault, get_asset_fault_history,
             get_asset_info_with_logs]

    agent_chain = create_agent(
        model=get_llm(),
        tools=tools,
        system_prompt=system_prompt
    )

    return agent_chain

