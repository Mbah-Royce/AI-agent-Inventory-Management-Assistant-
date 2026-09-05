import sqlite3

from langchain_core.tools import tool
from pydantic import BaseModel, Field, ValidationError
from .sql_queries import update_asset_status, get_asset_by_id, get_asset_data, retry_database_operation, \
    update_asset_location, log_asset_fault, db_conn, update_idempotency, insert_idempotency, get_idempotency_info
import uuid
import json


# ================================
# PYDANTIC
# ================================
# Enforcing type restrictions
class GetAssetInfo(BaseModel):
    asset_id: str = Field(description='asset id')


class UpdateAssetStatus(BaseModel):
    asset_status: str = Field(description='asset status')
    asset_id: str = Field(description='asset id')


class UpdateAssetLocation(BaseModel):
    asset_location: str = Field(description='asset location')
    asset_id: str = Field(description='asset id')


class LogAssetFault(BaseModel):
    asset_id: str = Field(description='asset id')
    asset_fault: str = Field(description='asset location')


@tool(args_schema=UpdateAssetStatus,
      description="""
        Change asset status using optimistic 
        Call get_asset first to obtain the current version
        Same idempotency key is used for retries
      """)
def change_asset_status(asset_status: str, asset_id: str) -> dict|str:
    try:

        with db_conn() as conn:

            # Created once for the logical operation
            # idempotency_key = str(uuid.uuid4())

            asset = get_asset_data(conn, asset_id)
            if asset:
                version = asset['version']

                # check idempotency
                # result = check_idempotency(conn=conn, idempotency_key=idempotency_key)

                rowcount = update_asset_status(conn, asset_id=asset_id, status=asset_status, current_version=version)
                # ------------
                # Detect conflict
                # -------------
                if rowcount == 0:

                    result = {
                        "success": False,
                        "error": "CONCURRENT_UPDATE",
                        "current_state": asset,
                    }

                    # update idempotency with info, concurrent update occurred
                    # update_idempotency(conn=conn, result=result, idempotency_key=idempotency_key)

                    return f'{json.dumps(result)}'

                # successful update
                result = {
                    "success": True,
                    "asset_id": asset_id,
                    "new_status": asset_status,
                    "new_version": version + 1,
                }

                # update idempotency with info, update successful
                # update_idempotency(conn=conn, idempotency_key=idempotency_key, result=result)
                return f'response {json.dumps(result)}'
                
            else:
                response = {
                    "success": True,
                    "error": "ASSET_NOT_FOUND",
                    "current_state": (
                        None
                    ),
                }
                return f'response {json.dumps(response)}'
    except Exception as e:
        return f'Error:{e}'


@tool(args_schema=UpdateAssetLocation, description='g')
def change_asset_location(asset_location: str, asset_id: str) -> dict:
    try:

        with db_conn() as conn:
            # Created once for the logical operation
            idempotency_key = str(uuid.uuid4())

            asset = get_asset_data(conn, asset_id)
            if asset:
                version = asset['version']
                rowcount = update_asset_location(conn,asset_id=asset_id, location=asset_location, current_version=version)

                # ------------
                # Detect conflict
                # -------------
                if rowcount == 0:
                    result = {
                        "success": False,
                        "error": "CONCURRENT_UPDATE",
                        "current_state": asset,
                    }

                    # update idempotency with info, concurrent update occurred
                    # update_idempotency(conn=conn, result=result, idempotency_key=idempotency_key)

                    return f'{json.dumps(result)}'
                
                # successful update
                result = {
                    "success": True,
                    "asset_id": asset_id,
                    "new_location": asset_location,
                    "new_version": version + 1,
                }

                return f'response {json.dumps(result)}'

            else:
                response = {
                    "success": True,
                    "error": "ASSET_NOT_FOUND",
                    "current_state": (
                        None
                    ),
                }
            return f'response {json.dumps(response)}'

    except Exception as e:
        return f'Error:{e}'



@tool(args_schema=LogAssetFault, description='create fault log for an asset')
def write_asset_fault_log(asset_fault: str, asset_id: str) -> str:
    try:

        with db_conn() as conn:
            # Created once for the logical operation
            idempotency_key = str(uuid.uuid4())

            asset = get_asset_data(conn, asset_id)
            if asset:
                results = log_asset_fault(conn, asset_id=asset_id, fault=asset_fault)
                if results == 1:
                    response = {
                        "success": True,
                        "asset_id": asset_id,
                        "fault": asset_fault,    
                    }
                    return f'response {json.dumps(response)}'
            else:
                response = {
                    "success": True,
                    "error": "ASSET_NOT_FOUND",
                    "current_state": (
                        None
                    ),
                }
                return f"response {response}"

    except Exception as e:
        return f"Error: {e}"


@tool(args_schema=GetAssetInfo, description='get asset fault history')
def get_asset_fault_history(asset_id: id) -> dict:
    pass


@tool(args_schema=GetAssetInfo, description=""""Get single asset info""")
def get_asset(asset_id: str) -> str:
    conn = None
    try:
        with db_conn() as conn:
            return f'response {json.dumps(get_asset_data(conn, asset_id))}'
    except Exception as e:
        return f'Error: {e}'



@tool(args_schema=GetAssetInfo, description='get an asset with associated logs')
def get_asset_info_with_logs(asset_id: str) -> str:
    try:
        conn = db_conn()
        return f'response {json.dumps(get_asset_data(conn, asset_id))}'
    except Exception as e:
        return f'Error: {e}'
    finally:
        conn.close()

def check_idempotency(conn, idempotency_key: str):

    existing = get_idempotency_info(conn, idempotency_key)

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
    insert_idempotency(idempotency_key, "asset_status_update", "processing")

    return existing