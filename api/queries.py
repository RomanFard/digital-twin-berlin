"""
SQL Queries for Trees API
همه کوئری‌ها اینجا متمرکز شدن که تغییرشون راحت باشه
"""

from config import SOURCE_SRID, OUTPUT_SRID

# ============================================
# Base SELECT Fields
# ============================================
# اگه خواستی فیلد اضافه/کم کنی، فقط اینجا رو عوض کن
TREE_FIELDS = """
    tree_id,
    ST_X(ST_Transform(geom, {output_srid})) AS lon,
    ST_Y(ST_Transform(geom, {output_srid})) AS lat,
    art_dtsch,
    art_bot,
    stammumfg,
    baumhoehe,
    kronedurch,
    pflanzjahr,
    bezirk,
    last_updated
""".format(output_srid=OUTPUT_SRID)

# ============================================
# Queries
# ============================================

def get_trees_query(bbox=None):
    """
    کوئری لیست درخت‌ها
    - bbox: اگه داده بشه، فقط درخت‌های تو محدوده
    """
    where_clauses = ["deleted_at IS NULL"]
    params = []
    
    if bbox:
        where_clauses.append(f"""
            ST_Within(
                ST_Transform(geom, {OUTPUT_SRID}),
                ST_MakeEnvelope(%s, %s, %s, %s, {OUTPUT_SRID})
            )
        """)
        params.extend([
            bbox["min_lon"],
            bbox["min_lat"],
            bbox["max_lon"],
            bbox["max_lat"]
        ])
    
    where_sql = " AND ".join(where_clauses)
    
    query = f"""
        SELECT {TREE_FIELDS}
        FROM trees_current
        WHERE {where_sql}
        ORDER BY tree_id
        LIMIT %s OFFSET %s
    """
    
    return query, params


def get_tree_by_id_query():
    """کوئری یه درخت خاص"""
    return f"""
        SELECT {TREE_FIELDS}
        FROM trees_current
        WHERE tree_id = %s
    """


def get_sync_status_query():
    """کوئری آخرین sync"""
    return """
        SELECT sync_batch_id, started_at, finished_at,
               records_read, records_inserted, records_updated,
               records_deleted, status
        FROM sync_log
        ORDER BY started_at DESC
        LIMIT 1
    """


def get_trees_count_query():
    """کوئری تعداد درخت‌ها"""
    return "SELECT COUNT(*) FROM trees_current WHERE deleted_at IS NULL;"