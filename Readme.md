# AI Inventory Management Agent

An AI-powered inventory management assistant that allows users to interact with an inventory database using natural-language commands.

The project uses **LangChain** to orchestrate the AI agent and its tool calls, with **SQLite** providing persistent data storage. The agent can interpret user requests, select the appropriate tool, and execute database operations through SQL queries.

The system also addresses two important challenges in agent-based applications: **concurrent updates (race conditions)** and **idempotency**.

---

## Features

* Natural-language interaction with inventory data
* AI agent orchestration using LangChain
* Pydantic used for data validation during tool calls
* SQLite database for persistent inventory storage
* Tool-based database operations using SQL
* Asset lookup and management
* Asset status updates
* Asset location updates
* Asset fault logging
* Optimistic concurrency control for concurrent updates
* Idempotency handling for duplicate operations
* Deterministic stub LLM for reliable testing
* Gemini LLM for real AI-powered interactions
* Command-line interface for submitting prompts
* Automated tests using pytest

---

## Architecture

At a high level, the application follows this flow:

```text
User
 │
 │ Natural-language prompt
 ▼
Command Line Interface
 │
 ▼
LangChain Agent
 │
 │ Determines required action
 ▼
Tool Call
 │
 ├── Get Asset
 ├── Change Asset Status
 ├── Change Asset Location
 └── Log Asset Fault
 │
 ▼
SQLite Database
 │
 ├── ASSETS
 ├── ASSET_FAULT_LOGS
 ├── idempotency_keys
 └── agent_operations
```

The LLM is responsible for determining **which tool should be called and with which arguments**. The tools are responsible for executing the corresponding database operations.

---

## Technology Stack

| Technology             | Purpose                           |
| ---------------------- | --------------------------------- |
| Python                 | Application development           |
| LangChain              | AI agent and tool orchestration   |
| Gemini                 | Production LLM                    |
| Deterministic Stub LLM | Predictable testing               |
| SQLite                 | Data persistence                  |
| SQL                    | Database operations               |
| pytest                 | Automated testing                 |
| uv                     | Project and dependency management |

---

## Project Setup

The project uses [`uv`](https://docs.astral.sh/uv/) for Python environment and dependency management.

### Prerequisites

* Python 3.10+
* uv
* Gemini API key

### Install dependencies

Clone the repository and install the project dependencies:

```bash
uv sync
```

For development and testing dependencies:

```bash
uv sync --dev
```

Initialise database:

```bash
uv run .\db\db_init.py
```

## Environment Configuration

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_api_key_here
USE_STUB=false
```

### Using Gemini

Set:

```env
USE_STUB=false
```

The application will use the Gemini chat model for agent interactions.

### Using the Stub LLM

Set:

```env
USE_STUB=true
```

The deterministic stub LLM is designed primarily for testing. Instead of making external LLM requests, it returns predictable tool calls based on the supplied prompt.

This makes tests:

* deterministic
* faster
* independent of external API availability
* less expensive
* easier to reproduce

---

## Running the Application

Prompts are supplied through command-line arguments.

For example:

```bash
uv run ai-agent "Get asset EQ10 information"
```

Other examples:

```bash
uv run ai-agent "Change EQ10 status to Broken"
```

```bash
uv run ai-agent "Change EQ10 location to Manchester"
```

```bash
uv run ai-agent "Log a low power fault for EQ10"
```

The agent interprets the prompt and determines which tool should be invoked.

---

## Agent Tools

The agent exposes tools that allow it to interact with the inventory database.

### Get Asset

Retrieves information about an asset using its asset ID.

Example request:

```text
Get asset EQ10 information
```

The agent generates a tool call similar to:

```text
get_asset(asset_id="EQ10")
```

The tool then executes the appropriate SQL query against SQLite.

### Change Asset Status

Updates the status of an asset.

Example:

```text
Change EQ10 status to Broken
```

The agent calls:

```text
change_asset_status(
    asset_id="EQ10",
    asset_status="Broken"
)
```

### Change Asset Location

Updates the location of an asset.

Example:

```text
Change EQ10 location to Manchester
```

### Log Asset Fault

Records a fault against an asset.

Example:

```text
Log a low power fault for EQ10
```

---

## Database

SQLite is used for data persistence.

The main tables are:

### `ASSETS`

Stores inventory information including:

* asset ID
* asset type
* location
* status
* version
* creation timestamp
* update timestamp

Example:

```text
asset_id | type      | location       | status | version
---------|-----------|----------------|--------|--------
EQ10     | Equipment | Warehouse One  | Active | 1
```

### `ASSET_FAULT_LOGS`

Stores faults associated with assets.

### `idempotency_keys`

Stores idempotency information for operations that should not be executed more than once.

### `agent_operations`

Tracks operations performed through the agent, including:

* operation ID
* idempotency key
* operation type
* resource ID
* operation status

---

# Concurrency and Race Conditions

A potential race condition exists when multiple requests attempt to modify the same asset concurrently.

For example, consider two agents attempting to update `EQ10`:

```text
Agent A                     Agent B
   │                           │
   │ Read version = 1          │
   │                           │
   │                           │ Read version = 1
   │                           │
   └───────────┬───────────────┘
               │
          Concurrent update
               │
               ▼
          SQLite database
```

Without concurrency control, both operations could potentially update the asset based on the same stale version.

### Optimistic Concurrency Control

The project uses an **optimistic concurrency approach** using the asset's `version` field.

The update is performed using a conditional SQL statement conceptually equivalent to:

```sql
UPDATE ASSETS
SET
    status = ?,
    version = version + 1
WHERE
    asset_id = ?
    AND version = ?;
```

The expected version is included in the `WHERE` clause.

If another operation has already modified the asset, the version will have changed and the update will affect zero rows.

This allows the application to detect the conflict rather than silently overwriting another update.

The expected behaviour for two concurrent updates is therefore:

```text
Request A → SUCCESS
Request B → CONFLICT
```

The test suite includes concurrent agent invocations to verify this behaviour.

---

# Idempotency

Idempotency is used to prevent the same logical operation from being performed multiple times.

This is important for agent-based systems because the same request may potentially be retried or submitted more than once.

For example:

```text
Request
idempotency_key = "111"
operation = Change EQ10 status to Broken
```

If the same operation is received again with the same idempotency key, the application can identify that the operation has already been processed rather than executing it again.

The `idempotency_keys` table is used to persist this information.

The `agent_operations` table provides an additional record of the operation and its state.

The combination allows the system to distinguish between:

```text
New operation
     ↓
Process operation
     ↓
Store result
```

and:

```text
Duplicate operation
     ↓
Existing idempotency key found
     ↓
Return existing result
```

This helps prevent duplicate side effects when operations are retried.

---

# Testing

The project uses **pytest** for automated testing.

Tests cover database operations, tool behaviour, agent behaviour, concurrency, and idempotency.

Run the complete test suite with:

```bash
uv run pytest
```

For verbose output:

```bash
uv run pytest -v
```

Run a specific test file:

```bash
uv run pytest tests/test_agent.py -v
```
"-s" flag can be added for avoiding shortcut and displaying of 'print()' output to terminal
---

## Deterministic Stub LLM

A deterministic stub LLM is included for agent testing.

Instead of making a request to Gemini, the stub returns predefined `AIMessage` responses containing the expected tool calls.

For example:

```text
User prompt
    ↓
"Get asset EQ10 information"
    ↓
DeterministicStubLLM
    ↓
get_asset(asset_id="EQ10")
    ↓
Real tool
    ↓
SQLite
```

This allows the agent workflow to be tested without relying on an external LLM service.

The stub also handles the subsequent tool response so that the complete agent execution can be tested:

```text
HumanMessage
     ↓
AIMessage + tool_call
     ↓
ToolMessage
     ↓
AIMessage final response
```

---

## Concurrency Testing

Concurrency tests execute multiple agent instances concurrently against the same SQLite database.

The test verifies that concurrent updates to the same asset do not result in both operations being accepted when they are based on the same asset version.

The expected result is:

```text
Agent A → successful update
Agent B → concurrency conflict
```

The test does not assume which agent wins because thread scheduling is nondeterministic.

Instead, it verifies the invariant:

```python
assert sorted(results) == ["conflict", "success"]
```

---

## Design Considerations

### Why SQLite?

SQLite was chosen because it provides:

* simple local persistence
* transactional support
* SQL-based data access
* minimal infrastructure requirements
* suitability for a small inventory management application

### Why LangChain?

LangChain provides the agent and tool orchestration layer, allowing natural-language requests to be translated into structured tool calls.

### Why a Stub LLM?

Tests should not depend on an external LLM service. The deterministic stub provides predictable responses while still allowing the LangChain agent and real tools to be exercised.

### Why Optimistic Concurrency?

Inventory updates can potentially be performed concurrently. Optimistic concurrency allows the application to detect stale updates without requiring long-running locks around the entire agent operation.

### Why Idempotency?

Agent operations can be retried or repeated. Idempotency prevents duplicate execution of operations that should only have one effect.

---

## Example Interaction

A user can issue:

```text
Change EQ10 status to Broken
```

The system processes the request approximately as follows:

```text
CLI
 │
 ▼
LangChain Agent
 │
 ▼
Gemini / Deterministic Stub
 │
 ▼
change_asset_status
 │
 ▼
Idempotency check
 │
 ▼
Version check
 │
 ▼
SQLite UPDATE
 │
 ▼
agent_operations
 │
 ▼
Agent response
```

The user does not need to construct SQL queries directly. The agent determines the appropriate operation and the tool layer handles interaction with the database.

---

## Project Structure

A typical project structure is:

```text
.
├── db/
│   └── db_init.py  
|
├── src/
│   └── ai_agent/
│       ├── __init__.py
│       ├── agent.py
│       ├── sql_queries.py
│       ├── tools.py
│       └── ...
│
├── tests/
│   ├── test_sql_queries.py
│   ├── test_tools.py
│   ├── test_agent.py
│   └── ...
│
├── .env
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## Future Improvements

Potential future improvements include:

* REST API integration
* authentication and authorization
* richer inventory search capabilities
* improved transaction management
* audit logging
* additional concurrency scenarios
* support for additional LLM providers
* more comprehensive end-to-end testing
* migration from SQLite to a server-based relational database for larger deployments

---

## Summary

This project demonstrates an AI-assisted inventory management system combining:

* **LangChain** for agent orchestration
* **Gemini** for natural-language reasoning
* **Deterministic Stub LLM** for reliable testing
* **SQLite** for persistence
* **SQL-based tools** for database operations
* **Optimistic concurrency control** for race-condition handling
* **Idempotency** for safe operation retries
* **pytest** for automated testing
* **uv** for project and dependency management

The primary goal is to demonstrate not only how an LLM can interact with a database through tools, but also how common challenges around **reliable state-changing operations, concurrency, retries, and testing** can be addressed in an agent-based application.


Note: Any apsect of this project should be used with care.
