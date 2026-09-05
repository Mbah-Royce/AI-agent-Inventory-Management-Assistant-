import sqlite3

# ================================
# DATABASE SETUP
# ================================
def init_db():
    # sqlite db setup
    conn = sqlite3.connect('inventory.db')
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

init_db()