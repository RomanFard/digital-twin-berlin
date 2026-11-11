"""
Generic queries for all feature types
"""
from config import OUTPUT_SRID


def get_all_types_query():
    """Get all feature types metadata"""
    return """
        SELECT id, code, name_fa, name_en, name_de, icon, color, geometry_type, source_url
        FROM feature_types
        WHERE is_active = TRUE
        ORDER BY id
    """


def get_features_query(type_codes=None, bbox=None, strname=None):
    """
    Get features with optional filters
    - type_codes: list of type codes (e.g., ['tree', 'bench'])
    - bbox: dict {min_lon, max_lon, min_lat, max_lat}
    """
    where_clauses = ["f.deleted_at IS NULL"]
    params = []

    if type_codes:
        placeholders = ",".join(["%s"] * len(type_codes))
        where_clauses.append(f"f.type_code IN ({placeholders})")
        params.extend(type_codes)

    if bbox:
   
        where_clauses.append(f"""
            ST_Within(
                ST_Transform(f.geom, {OUTPUT_SRID}),
                ST_MakeEnvelope(%s, %s, %s, %s, {OUTPUT_SRID})
            )
        """)
        params.extend([
            bbox["min_lon"], bbox["min_lat"],
            bbox["max_lon"], bbox["max_lat"]
        ])
    if strname:
        where_clauses.append("""
            EXISTS (
                SELECT 1 FROM feature_attributes a
                WHERE a.feature_id = f.feature_id
                  AND a.attr_name = 'strname'
                  AND a.attr_value::text ILIKE %s
            )
        """)
        params.append(f'%{strname}%')
    where_sql = " AND ".join(where_clauses)

    query = f"""
        SELECT
            f.feature_id,
            f.type_code,
            ft.icon,
            ft.color,
            ST_X(ST_Transform(f.geom, {OUTPUT_SRID})) AS lon,
            ST_Y(ST_Transform(f.geom, {OUTPUT_SRID})) AS lat,
            f.last_updated,
            (
                SELECT jsonb_object_agg(a.attr_name, a.attr_value)
                FROM feature_attributes a
                WHERE a.feature_id = f.feature_id
            ) AS attributes
        FROM features f
        JOIN feature_types ft ON f.type_code = ft.code
        WHERE {where_sql}
        ORDER BY f.feature_id
        LIMIT %s OFFSET %s
    """
    return query, params


def get_feature_by_id_query():
    """Get single feature by ID"""
    return f"""
        SELECT
            f.feature_id,
            f.type_code,
            ft.icon,
            ft.color,
            ST_X(ST_Transform(f.geom, {OUTPUT_SRID})) AS lon,
            ST_Y(ST_Transform(f.geom, {OUTPUT_SRID})) AS lat,
            f.last_updated,
            (
                SELECT jsonb_object_agg(a.attr_name, a.attr_value)
                FROM feature_attributes a
                WHERE a.feature_id = f.feature_id
            ) AS attributes
        FROM features f
        JOIN feature_types ft ON f.type_code = ft.code
        WHERE f.feature_id = %s
    """


def get_scene_query(type_codes=None, bbox=None):
    """
    For Unreal: get all features in a bbox (multi-type)
    """
    return get_features_query(type_codes, bbox)


def get_stats_query():
    """Get statistics per type"""
    return """
        SELECT
            ft.code AS type_code,
            ft.name_en,
            ft.icon,
            ft.color,
            COUNT(f.feature_id) FILTER (WHERE f.deleted_at IS NULL) AS active,
            COUNT(f.feature_id) FILTER (WHERE f.deleted_at IS NOT NULL) AS deleted,
            COUNT(f.feature_id) AS total
        FROM feature_types ft
        LEFT JOIN features f ON f.type_code = ft.code
        WHERE ft.is_active = TRUE
        GROUP BY ft.code, ft.name_en, ft.icon, ft.color
        ORDER BY ft.code
    """


def get_count_by_bezirk_query(type_code='tree'):
    """Count features by bezirk (for trees)"""
    return """
        SELECT
            a.attr_value #>> '{}' AS bezirk,
            COUNT(*) AS count
        FROM feature_attributes a
        JOIN features f ON f.feature_id = a.feature_id
        WHERE a.attr_name = 'bezirk'
          AND f.type_code = %s
          AND f.deleted_at IS NULL
        GROUP BY a.attr_value
        ORDER BY count DESC
    """
def get_features_in_polygon_query(polygon_wkt, type_codes=None, limit=1000, offset=0):
    """
    Get features inside a polygon (WKT format)
    """
    where_clauses = ["f.deleted_at IS NULL"]
    params = []

    if polygon_wkt:
        where_clauses.append(f"""
            ST_Within(
                f.geom,
                ST_Transform(ST_GeomFromText(%s, 4326), 25833)
            )
        """)
        params.append(polygon_wkt)

    if type_codes:
        placeholders = ",".join(["%s"] * len(type_codes))
        where_clauses.append(f"f.type_code IN ({placeholders})")
        params.extend(type_codes)

    where_sql = " AND ".join(where_clauses)

    query = f"""
        SELECT
            f.feature_id,
            f.type_code,
            ft.icon,
            ft.color,
            ST_X(ST_Transform(f.geom, {OUTPUT_SRID})) AS lon,
            ST_Y(ST_Transform(f.geom, {OUTPUT_SRID})) AS lat,
            f.last_updated,
            (
                SELECT jsonb_object_agg(a.attr_name, a.attr_value)
                FROM feature_attributes a
                WHERE a.feature_id = f.feature_id
            ) AS attributes
        FROM features f
        JOIN feature_types ft ON f.type_code = ft.code
        WHERE {where_sql}
        ORDER BY f.feature_id
        LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])
    return query, params