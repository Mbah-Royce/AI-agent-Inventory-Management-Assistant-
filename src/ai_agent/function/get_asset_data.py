from ..utils import db_conn
def get_asset_data(asset_id: str):
    conn = db_conn()

    try:
        current = conn.execute(
            """
                SELECT asset_id, version, status, location
                FROM ASSETS
                WHERE asset_id = ?
            """, 
            (asset_id,),
        ).fetchone()
        return dict(current) if current else None
    except Exception as e:
        print(f"Error {e}")
    finally:
        conn.close()
