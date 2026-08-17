import sqlite3

from langchain_core.tools import tool
from pydantic import BaseModel, Field, ValidationError
from sql_queries import update_asset_status, get_asset_by_id, get_asset_data, retry_database_operation, \
    update_asset_location, log_asset_fault
import uuid


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
def change_asset_status(asset_status: str, asset_id: str) -> dict:
    try:

        # Created once for the logical operation
        idempotency_key = str(uuid.uuid4())

        asset = get_asset_data(asset_id)
        if asset:
            version = asset['version']
            return update_asset_status(asset_id=asset_id, status=asset_status, current_version=version,
                                       idempotency_key=idempotency_key)
        else:
            return {
                "success": True,
                "error": "ASSET_NOT_FOUND",
                "current_state": (
                    None
                ),
            }
    except Exception as e:
        raise


@tool(args_schema=UpdateAssetLocation, description='g')
def change_asset_location(asset_location: str, asset_id: str) -> dict:
    try:
        # Created once for the logical operation
        idempotency_key = str(uuid.uuid4())

        asset = get_asset_data(asset_id)
        if asset:
            version = asset['version']
            return update_asset_location(asset_id=asset_id, location=asset_location, current_version=version,
                                         idempotency_key=idempotency_key)
        else:
            return {
                "success": True,
                "error": "ASSET_NOT_FOUND",
                "current_state": (
                    None
                ),
            }

    except Exception as e:
        raise


@tool(args_schema=LogAssetFault, description='create fault log for an asset')
def log_asset_fault(asset_fault: str, asset_id: str) -> dict:
    try:
        # Created once for the logical operation
        idempotency_key = str(uuid.uuid4())

        asset = get_asset_data(asset_id)
        if asset:
            return log_asset_fault(asset_id=asset_id, fault=asset_fault,
                                   idempotency_key=idempotency_key)
        else:
            return {
                "success": True,
                "error": "ASSET_NOT_FOUND",
                "current_state": (
                    None
                ),
            }

    except Exception as e:
        raise


@tool(args_schema=GetAssetInfo, description='get asset fault history')
def get_asset_fault_history(asset_id: id) -> dict:
    pass


@tool(args_schema=GetAssetInfo, description=""""
Get single asset info""")
def get_asset(asset_id: str) -> str:
    try:
        return get_asset_data(asset_id)
    except Exception:
        raise


@tool(args_schema=GetAssetInfo, description='get an asset with associated logs')
def get_asset_info_with_logs(asset_id: id) -> str:
    pass
