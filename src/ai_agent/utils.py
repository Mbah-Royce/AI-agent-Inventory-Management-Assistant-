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
from .tools import (change_asset_location, change_asset_status, write_asset_fault_log, get_asset_fault_history, get_asset
                   ,get_asset_info_with_logs)
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv



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
        last_message = messages[-1]
        print("\n--- STUB RECEIVED ---")
        print("TYPE:", last_message.type)
        print("CONTENT:", last_message.content)
        prompt = str(messages[-1].content).lower()

        # Get user text
        # prompt = "\n".join(
        #     str(message.content)
        #     for message in messages
        # ).lower()

        # Deterministic decision
        if messages[-1].type == "tool":
            # Give final answer after tool execution
            response = AIMessage(
            content=f"Tool result: {last_message.content}"
        )

            return ChatResult(
                generations=[
                    ChatGeneration(message=response)
                ]
            )
        elif "change" in prompt and "status" in prompt and "de10" in prompt:

            response = AIMessage(
                content="yes",
                tool_calls=[
                    {
                        "name": "change_asset_status",
                        "args": {
                            "asset_id": "DE10",
                            "asset_status": "Out of Service",
                        },
                        "id": "stub-change-status-eq10",
                        "type": "tool_call",
                    }
                ],
            )
        elif "change" in prompt and "status" in prompt:

            response = AIMessage(
                content="yes",
                tool_calls=[
                    {
                        "name": "change_asset_status",
                        "args": {
                            "asset_id": "EQ10",
                            "asset_status": "Inactive",
                        },
                        "id": "stub-change-status-eq10",
                        "type": "tool_call",
                    }
                ],
            )
        elif "change " in prompt and "location" in prompt:

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
                        "type": "tool_call"
                    }
                ],
            )
        elif "log" in prompt and "fault" in prompt:

            response = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "write_asset_fault_log",
                        "args": {
                            "asset_id": "EQ10",
                            "asset_fault": "low power output",
                        },
                        "id": "stub-change-location-eq10",
                        "type": "tool_call"
                    }
                ],
            )
        elif "get" in prompt and "asset" in prompt:

            response = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_asset",
                        "args": {
                            "asset_id": "EQ10",
                        },
                        "id": "stub-get-asset-Eq10",
                        "type": "tool_call"
                    }
                ],
            )
        else:
            response = AIMessage(
                content=f"STUB: No matching action for the prompt:{prompt}"
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
def get_llm():
    load_dotenv()
    if os.getenv('USE_STUB').lower() == 'true':
        print("Using Deterministic LLM")
        return DeterministicStubLLM()
    try:
        # os.environ["GOOGLE_API_KEY"] = os.getenv('GEMINI_API_KEY')
        llm = ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            google_api_key= os.getenv('GEMINI_API_KEY'),
        )
        return llm
    except Exception as e:
        print(f"Local model unavailable: {e}")
        print("Local model not found. Falling back to stub")
        return DeterministicStubLLM()


# ================================
# AGENT SETUP
# ================================
tools = [change_asset_status, change_asset_location, write_asset_fault_log, get_asset_fault_history, get_asset]

def agent_create(system_prompt, model=get_llm()):
    # tools = [change_asset_status, change_asset_location, write_asset_fault_log, get_asset_fault_history, get_asset]

    agent_chain = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt
    )

    return agent_chain

