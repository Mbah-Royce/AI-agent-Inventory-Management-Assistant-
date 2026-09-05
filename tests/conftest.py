import sqlite3
import pytest

@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    try:
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ASSETS(
                asset_id TEXT PRIMARY KEY,
                type TEXT UNIQUE NOT NULL CHECK(type IN('Equipment','Vehicle','Device')),
                location TEXT NOT NULL,
                status TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                created_at TEXT DEFAULT "2026-09-04 11:30:00",
                updated_at TEXT DEFAULT "2026-09-04 11:30:00"
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ASSET_FAULT_LOGS(
                assets_fault_log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                fault TEXT NOT NULL,
                created_at TEXT DEFAULT "2026-09-04 11:30:00",
                updated_at TEXT DEFAULT "2026-09-04 11:30:00",
                asset_id TEXT,
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
                       "values ('EQ10','Equipment','Warehouse One','Active')")
        cursor.execute("INSERT OR IGNORE INTO ASSETS (asset_id,type,location,status) "
                       "values ('DE10','Device','warehouse_main','quarantine')")
        cursor.execute("INSERT OR IGNORE INTO ASSETS (asset_id,type,location,status) "
                       "values ('VE11','Vehicle','warehouse_main','Active')")

        cursor.execute("INSERT OR IGNORE INTO ASSET_FAULT_LOGS (asset_id,fault) "
                       "values ('EQ10', 'jammed motor')")
        cursor.execute("INSERT OR IGNORE INTO ASSET_FAULT_LOGS (asset_id,fault) "
                       "values ('DE10','broken screw')")
        cursor.execute("INSERT OR IGNORE INTO ASSET_FAULT_LOGS (asset_id,fault) "
                       "values ('VE10','low battery')")

        cursor.execute("INSERT OR IGNORE INTO idempotency_keys (idempotency_key,response,status) "
                               "values ('111','asset_status_update','processing')")
        cursor.execute("INSERT OR IGNORE INTO idempotency_keys (idempotency_key,response,status) "
                               "values ('222','data_json', 'completed')")

        conn.commit()

        yield conn
    except Exception:
        raise
    finally:
        conn.close()

@pytest.fixture
def db_agent_test(path="tests/test.db"):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row

    try:
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ASSETS(
                asset_id TEXT PRIMARY KEY,
                type TEXT UNIQUE NOT NULL CHECK(type IN('Equipment','Vehicle','Device')),
                location TEXT NOT NULL,
                status TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                created_at TEXT DEFAULT "2026-09-04 11:30:00",
                updated_at TEXT DEFAULT "2026-09-04 11:30:00"
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ASSET_FAULT_LOGS(
                assets_fault_log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                fault TEXT NOT NULL,
                created_at TEXT DEFAULT "2026-09-04 11:30:00",
                updated_at TEXT DEFAULT "2026-09-04 11:30:00",
                asset_id TEXT,
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
                       "values ('EQ10','Equipment','Warehouse One','Active')")
        cursor.execute("INSERT OR IGNORE INTO ASSETS (asset_id,type,location,status) "
                       "values ('DE10','Device','warehouse_main','quarantine')")
        cursor.execute("INSERT OR IGNORE INTO ASSETS (asset_id,type,location,status) "
                       "values ('VE11','Vehicle','warehouse_main','Active')")

        cursor.execute("INSERT OR IGNORE INTO ASSET_FAULT_LOGS (asset_id,fault) "
                       "values ('EQ10', 'jammed motor')")
        cursor.execute("INSERT OR IGNORE INTO ASSET_FAULT_LOGS (asset_id,fault) "
                       "values ('DE10','broken screw')")
        cursor.execute("INSERT OR IGNORE INTO ASSET_FAULT_LOGS (asset_id,fault) "
                       "values ('VE10','low battery')")

        cursor.execute("INSERT OR IGNORE INTO idempotency_keys (idempotency_key,response,status) "
                               "values ('111','asset_status_update','processing')")
        cursor.execute("INSERT OR IGNORE INTO idempotency_keys (idempotency_key,response,status) "
                               "values ('222','data_json', 'completed')")

        conn.commit()

        return path
    except Exception:
        raise
    finally:
        conn.close()