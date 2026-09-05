from ai_agent.tools import get_asset, update_asset_status
from unittest.mock import patch

def test_get_asset_by_id(db):

    with patch("ai_agent.tools.db_conn", return_value=db):
        result = get_asset.invoke({
            "asset_id":'VE11'
        })

        assert result.startswith("response ")
        assert '"asset_id": "VE11"' in result

def test_change_asset_status(db):

    with patch("ai_agent.tools.db_conn", return_value=db):
        result = update_asset_status.invoke({
            "asset_id":'VE11',
            "asset_status": 'Obliterated'
        })

        assert result.startswith("response ")
        assert '"new_version": "VE11"' in result


    
