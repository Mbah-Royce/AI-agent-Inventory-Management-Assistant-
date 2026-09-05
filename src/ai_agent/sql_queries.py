# from uitls import db_conn
import json
import random
import sqlite3
import os
import time
from dotenv import load_dotenv
from contextlib import contextmanager

get_asset_by_id = """
    SELECT asset_id, version, status, location
    FROM ASSETS
    WHERE asset_id = ?
"""

@contextmanager
def db_conn(path='db/inventory.db'):
    load_dotenv()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def insert_idempotency(conn, idempotency_key, status, response):
    try:
        conn.execute('''
        INSERT INTO idempotency_keys(
            idempotency_key,
            response,
            status
        )
        VALUES (?,?,?)
        ''', (
            idempotency_key,
            status,
            response
        ),)
        conn.commit()
        return {
            'idempotency_key':idempotency_key
        }
    except Exception:
        conn.rollback()
        raise

def update_idempotency(conn, result: dict, idempotency_key: str) -> int:

    try:
        cursor = conn.execute(
                '''
                UPDATE idempotency_keys
                SET
                 status=?,
                 response=?
                WHERE idempotency_key=?
                ''',
                (
                    "completed",
                    json.dumps(result),
                    idempotency_key,
                )
            )
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        conn.rollback()
        raise    

def update_asset_status(conn, asset_id: str, status: str, current_version: int) -> int:

    try:
        cursor = conn.execute(
            """
            UPDATE ASSETS
            SET 
                status = ?,
                version = version + 1
            WHERE
                asset_id = ?
                AND version = ?
            """,
            (
                status,
                asset_id,
                current_version
            )
        )
        conn.commit()
        return cursor.rowcount
    except Exception:
        conn.rollback()
        raise

def update_asset_location(conn, asset_id: str, location: str, current_version: int) -> int:
    try:
        
        # concurrency update
        cursor = conn.execute(
            """
            UPDATE ASSETS
            SET 
                location = ?,
                version = version + 1
            WHERE
                asset_id = ?
                AND version = ?
            """,
            (
                location,
                asset_id,
                current_version
            )
        )
        conn.commit()
        return cursor.rowcount
        
    except Exception:
        conn.rollback()
        raise

def log_asset_fault(conn, asset_id: str, fault: str):

    try:

        conn.execute('''
                INSERT INTO asset_fault_logs(
                    fault,
                    asset_id
                )
                VALUES (?,?)
            ''', (
            fault,
            asset_id
        )
        )

        conn.commit()
        return 1

    except Exception as e:
        conn.rollback()
        raise

def get_asset_data(conn, asset_id: str) -> dict:
    try:
        current = conn.execute(
            """
                SELECT asset_id, version, status, type, location, created_at, updated_at
                FROM ASSETS
                WHERE asset_id = ?
            """, 
            (asset_id,),
        ).fetchone()
        return dict(current) if current else None
    except Exception as e:
        raise

def get_idempotency_info(conn, idempotency_key: str) -> dict:
    try:
        current = conn.execute(
        '''
        SELECT idempotency_key, status, response
        FROM idempotency_keys
        WHERE idempotency_key = ?
        ''',
        (idempotency_key,),
    ).fetchone()
        return dict(current) if current else None
    except Exception as e:
        raise

def retry_database_operation(operation, idempotency_key, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return operation(idempotency_key)
        except sqlite3.OperationalError as e:
            error = str(e).lower()
            if 'locked' not in error and 'busy' not in error:
                raise
            if attempt == max_attempts - 1:
                raise
            delay = (
                    0.1 * (2 ** attempt) + random.uniform(0, 0.1)
            )
            time.sleep(delay)
