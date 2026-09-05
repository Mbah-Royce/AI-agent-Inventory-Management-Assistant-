import sqlite3
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from .utils import agent_create, init_db, get_llm
import sys
from ai_agent.config import system_prompt


def main():

    if len(sys.argv) < 2:
        print("prompt needed")
        sys.exit(1)
    
    verbose_flag = False
    if len(sys.argv) == 3 and sys.argv[2] == '--verbose':
        verbose_flag = True

    prompt = sys.argv[1]

    load_dotenv()

    # set system prompt
    system_prompt = system_prompt

    # create agent
    agent = agent_create(system_prompt)

    response = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        }
    )

    for message in response["messages"]:
        print("\nTYPE:", type(message))
        print("CONTENT:", message.content)

        if getattr(message, "tool_calls", None):
            print("🔧 TOOL CALLS:")
            for call in message.tool_calls:
                print("Tool:", call["name"])
                print("Args:", call["args"])
    # return response


    # def run_agent():
    #     result = agent.invoke(
    #         {
    #             "messages": [
    #                 {
    #                     "role": "user",
    #                     "content": "change status with id EQ10 is now destroyed",
    #                 }
    #             ]
    #         }
    #     )

    #     return result


    # with ThreadPoolExecutor(max_workers=2) as executor:
    #     results = list(
    #         executor.map(
    #             lambda _: run_agent(),
    #             range(2),
    #         )
    #     )

    # print(result)

    # failure_counter = {
    #     "count": 0
    # }
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

if __name__ == "__main__":
    main()