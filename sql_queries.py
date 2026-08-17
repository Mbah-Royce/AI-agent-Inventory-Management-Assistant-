# from uitls import db_conn
import json
import random
import sqlite3
import os
import time

get_asset_by_id = """
    SELECT asset_id, version, status, location
    FROM ASSETS
    WHERE asset_id = ?
"""


def db_conn():
    conn = sqlite3.connect(os.getenv('DB_NAME'))
    conn.row_factory = sqlite3.Row
    return conn


def check_idempotency(conn, idempotency_key: str):
    existing = conn.execute(
        '''
        SELECT status, response
        FROM idempotency_keys
        WHERE idempotency_key = ?
        ''',
        (idempotency_key,),
    ).fetchone()

    dict(existing) if existing else None

    if existing:
        if existing['status'] == 'completed':
            return json.loads(existing["response"])
        else:
            return {
                "success": False,
                "error": "OPERATION_IN_PROGRESS"
            }

    # register operation
    conn.execute('''
        INSERT INTO idempotency_keys(
            idempotency_key,
            response,
            status
        )
        VALUES (?,?,?)
    ''', (
        idempotency_key,
        "asset_status_update",
        "processing"
    ),
                 )


def update_idempotency(conn, result: dict, idempotency_key: str):
    conn.execute(
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


def update_asset_status(asset_id: str, status: str, current_version: int, idempotency_key: str):
    conn = db_conn()

    try:
        # check idempotency
        check_idempotency(conn=conn, idempotency_key=idempotency_key)

        # concurrency update
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
        # ------------
        # Detect conflict
        # -------------
        if cursor.rowcount == 0:
            current = conn.execute(
                get_asset_by_id, (asset_id,),
            ).fetchone()

            result = {
                "success": False,
                "error": "CONCURRENT_UPDATE",
                "current_state": (
                    dict(current) if current else None
                ),
            }

            # update idempotency with info, concurrent update occurred
            update_idempotency(conn=conn, result=result, idempotency_key=idempotency_key)

            conn.commit()

            return result

        # successful update
        result = {
            "success": True,
            "asset_id": asset_id,
            "new_status": status,
            "new_version": current_version + 1,
        }

        # update idempotency with info, update successful
        update_idempotency(conn=conn, idempotency_key=idempotency_key, result=result)
        conn.commit()
        return result
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_asset_location(asset_id: str, location: str, current_version: int, idempotency_key: str):
    conn = db_conn()

    try:
        # check idempotency
        check_idempotency(conn=conn, idempotency_key=idempotency_key)

        # concurrency update
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
                location,
                asset_id,
                current_version
            )
        )
        # ------------
        # Detect conflict
        # -------------
        if cursor.rowcount == 0:
            current = conn.execute(
                get_asset_by_id, (asset_id,),
            ).fetchone()

            result = {
                "success": False,
                "error": "CONCURRENT_UPDATE",
                "current_state": (
                    dict(current) if current else None
                ),
            }

            # update idempotency with info, concurrent update occurred
            update_idempotency(conn=conn, result=result, idempotency_key=idempotency_key)

            conn.commit()

            return result

        # successful update
        result = {
            "success": True,
            "asset_id": asset_id,
            "new_location": location,
            "new_version": current_version + 1,
        }

        # update idempotency with info, update successful
        update_idempotency(conn=conn, idempotency_key=idempotency_key, result=result)
        conn.commit()
        return result
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def log_asset_fault(asset_id: str, fault: str, idempotency_key: str):
    conn = db_conn()

    try:

        # check idempotency
        check_idempotency(conn=conn, idempotency_key=idempotency_key)

        conn.execute('''
                INSERT INTO asset_fault_logs(
                    fault,
                    asset_id,
                )
                VALUES (?,?)
            ''', (
            fault,
            asset_id,
        ),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_asset_data(asset_id: str):
    conn = db_conn()

    try:
        current = conn.execute(
            get_asset_by_id, (asset_id,),
        ).fetchone()
        return dict(current) if current else None
    except Exception:
        raise
    finally:
        conn.close()


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
