from ai_agent.sql_queries import get_asset_data, update_asset_location, update_asset_status, log_asset_fault, update_idempotency, insert_idempotency, get_idempotency_info

def test_get_asset_by_id(db):

    result = get_asset_data(db, 'EQ10')

    db.close()

    assert result == {
            "asset_id": "EQ10",
            "version": 1,
            "status": "Active",
            "type": "Equipment",
            "location": "Warehouse One",
            "created_at": "2026-09-04 11:30:00",
            "updated_at": "2026-09-04 11:30:00",
        }

def test_update_asset_status(db):
    result = update_asset_status(db, 'EQ10','Inactive', 1)

    db.close()

    assert type(result) == int
    assert result != 0

def test_update_asset_location(db):
    result = update_asset_location(db, 'EQ10','Warehouse Two', 1)

    db.close()

    assert type(result) == int
    assert result != 0

def test_check_insert_idempotency(db):

    result = insert_idempotency(db, '333','progress', "data_json_response")

    db.close()

    assert result == {
            'idempotency_key':'333'
        }

def test_insert_idempotency(db):

    result = insert_idempotency(db, '333','progress', "data_json_response")

    db.close()

    assert result == {
            'idempotency_key':'333'
        }

def test_update_idempotency(db):

    result = update_idempotency(db, "data_json_response", "111")

    db.close()

    assert type(result) == int
    assert result != 0

def test_get_idempotency(db):

    result = get_idempotency_info(db, '111')

    db.close()

    assert result == {
            "idempotency_key": "111",
            "response": "asset_status_update",
            "status": "processing",
        }

def test_log_asset_fault(db):
    result = log_asset_fault(db, "EQ10", "Broken belt",)

    db.close()

    assert type(result) == int
    assert result != 0