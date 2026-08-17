import sqlite3
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from uitls import agent_create, init_db, get_llm

load_dotenv()

# initialise database
# init_db()

# set system prompt
system_prompt = """
You are inventory tracking agent. Be concise and precise
Your primary objective is to maintain accurate real-time information
relating to assets (devices, equipments, vehicle) updating records, inserting records
of assets and asset fault in an sqlite database.
Do not get guess any data, always verify from database

# Available tools
- change_asset_status: modify status of an asset
- get_asset:retrieves information about an assets

# Interaction style
- Tone: professional, objective and direct.
- Format: Acknowledge the request, state the total action taken and provide clear summary of the action.

# Error Handling
- Present error that easy to understand and propose possible solution to handle error a user can understand
with no technical information
"""
# create agent
agent = agent_create(system_prompt)

result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "change status with id EQ10 is now destroyed",
            }
        ]
    }
)


def run_agent():
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "change status with id EQ10 is now destroyed",
                }
            ]
        }
    )

    return result


with ThreadPoolExecutor(max_workers=2) as executor:
    results = list(
        executor.map(
            lambda _: run_agent(),
            range(2),
        )
    )

print(result)

failure_counter = {
    "count": 0
}
# def flaky_approve_order(
#     asset_id,
#     asset_status,
#     idempotency_key,
# ):
#     failure_counter["count"] += 1
#
#     print(
#         f"Database attempt {failure_counter['count']}"
#     )
#
#     print(
#         f"Idempotency key: {idempotency_key}"
#     )
#
#     # Simulate a transient database failure
#     if failure_counter["count"] == 1:
#         raise sqlite3.OperationalError(
#             "database is locked"
#         )
#
#     return change_asset_status(
#         asset_id=asset_id,
#         asset_status=asset_status,
#         idempotency_key=idempotency_key,
#     )

# Invoke the chain locally on your machine
# response = chain.invoke({"question": "Why is the sky blue?"})
# print(response)
