from ai_agent.tools import get_asset, change_asset_status, change_asset_location, write_asset_fault_log
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
        result = change_asset_status.invoke({
            "asset_id":'VE11',
            "asset_status": 'Obliterated'
        })

        assert result.startswith("response ")
        assert '"new_version": 2' in result
        assert '"new_status": "Obliterated"' in result

def test_change_asset_status_old_version(db, monkeypatch):
    monkeypatch.setattr(
        "ai_agent.tools.get_asset_data",
        lambda conn, asset_id :{"version":100},
    )
    with patch("ai_agent.tools.db_conn", return_value=db):
        result = change_asset_status.invoke({
            "asset_id":'VE11',
            "asset_status": 'Obliterated'
        })

        assert '"error": "CONCURRENT_UPDATE"' in result

def test_change_asset_status_asset_not_found(db, monkeypatch):

    with patch("ai_agent.tools.db_conn", return_value=db):
        result = change_asset_status.invoke({
            "asset_id":'VE111',
            "asset_status": 'Obliterated'
        })

        assert '"error": "ASSET_NOT_FOUND"' in result
    
def test_change_asset_location(db):
    
    with patch("ai_agent.tools.db_conn", return_value=db):
        result = change_asset_location.invoke({
            "asset_id":'VE11',
            "asset_location": 'Manchester'
        })

        assert result.startswith("response ")
        assert '"new_version": 2' in result
        assert '"new_location": "Manchester"' in result

def test_write_asset_fault_log(db):
    
    with patch("ai_agent.tools.db_conn", return_value=db):
        result = write_asset_fault_log.invoke({
            "asset_id":'EQ10',
            "asset_fault": 'Bad CPU'
        })
        print(result)
        assert result.startswith("response ")
        assert '1' in result


