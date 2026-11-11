"""
Queries for zones
"""

def get_all_zones_query():
    """لیست همه Zoneها"""
    return """
        SELECT
            zone_id::text,
            name,
            description,
            ST_AsGeoJSON(polygon)::json AS polygon,
            filters,
            rules,
            is_active,
            created_at,
            updated_at
        FROM zones
        WHERE is_active = TRUE
        ORDER BY created_at DESC
    """


def get_zone_by_id_query():
    """یه Zone خاص"""
    return """
        SELECT
            zone_id::text,
            name,
            description,
            ST_AsGeoJSON(polygon)::json AS polygon,
            filters,
            rules,
            is_active,
            created_at,
            updated_at
        FROM zones
        WHERE zone_id = %s
    """


def create_zone_query():
    """ساخت Zone جدید"""
    return """
        INSERT INTO zones (name, description, polygon, filters, rules)
        VALUES (
            %s,
            %s,
            ST_GeomFromGeoJSON(%s),
            %s,
            %s
        )
        RETURNING zone_id::text
    """


def update_zone_query():
    """آپدیت Zone"""
    return """
        UPDATE zones
        SET
            name = COALESCE(%s, name),
            description = COALESCE(%s, description),
            polygon = COALESCE(ST_GeomFromGeoJSON(%s), polygon),
            filters = COALESCE(%s, filters),
            rules = COALESCE(%s, rules),
            is_active = COALESCE(%s, is_active),
            updated_at = NOW()
        WHERE zone_id = %s
        RETURNING zone_id::text
    """


def delete_zone_query():
    """حذف Zone"""
    return """
        DELETE FROM zones
        WHERE zone_id = %s
        RETURNING zone_id::text
    """


def get_features_in_zone_query(zone_id):
    """
    درختان داخل یه Zone رو برمی‌گردونه
    """
    return """
        SELECT
            f.feature_id,
            f.type_code,
            ft.icon,
            ft.color,
            ST_X(ST_Transform(f.geom, 4326)) AS lon,
            ST_Y(ST_Transform(f.geom, 4326)) AS lat,
            f.last_updated,
            (
                SELECT jsonb_object_agg(a.attr_name, a.attr_value)
                FROM feature_attributes a
                WHERE a.feature_id = f.feature_id
            ) AS attributes
        FROM features f
        JOIN feature_types ft ON f.type_code = ft.code
        JOIN zones z ON z.zone_id = %s
               WHERE f.deleted_at IS NULL
          AND ST_Within(
                ST_Transform(f.geom, 4326),
                z.polygon
              )
          AND ST_Within(
                ST_Transform(f.geom, 4326),
                ST_MakeEnvelope(13.35, 52.47, 13.50, 52.53, 4326)
              )
        ORDER BY f.feature_id
        LIMIT 50000
    """
def deactivate_all_zones_query():
    """غیرفعال کردن همه Zoneها"""
    return "UPDATE zones SET is_active = FALSE WHERE is_active = TRUE;"


def activate_zone_query():
    """فعال کردن یه Zone خاص"""
    return """
        UPDATE zones
        SET is_active = TRUE, updated_at = NOW()
        WHERE zone_id = %s
        RETURNING zone_id::text
    """


def get_active_zone_query():
    """گرفتن Zone فعال"""
    return """
        SELECT
            zone_id::text,
            name,
            description,
            ST_AsGeoJSON(polygon)::json AS polygon,
            filters,
            rules,
            is_active,
            created_at,
            updated_at
        FROM zones
        WHERE is_active = TRUE
        LIMIT 1
    """