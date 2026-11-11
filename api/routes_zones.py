from fastapi import APIRouter, HTTPException
from typing import List
import json
from database import get_connection, return_connection
from schemas_zones import Zone, ZoneCreate, ZoneUpdate
import queries_zones

router = APIRouter(prefix="/api/zones", tags=["zones"])
@router.get("/active/scene")
def get_active_zone_scene():
    """
    برای Unreal: Zone فعال + درختانش رو برمی‌گردونه
    """
    conn = get_connection()
    try:
        # ۱. Zone فعال رو بگیر
        cur = conn.cursor()
        cur.execute(queries_zones.get_active_zone_query())
        zone_row = cur.fetchone()
        
        if not zone_row:
            cur.close()
            return {
                "zone": None,
                "total_count": 0,
                "features": [],
                "message": "No active zone"
            }
        
        zone_id = zone_row[0]
        zone_info = {
            "zone_id": zone_row[0],
            "name": zone_row[1],
            "description": zone_row[2],
            "filters": zone_row[4],
            "rules": zone_row[5]
        }
        
        # ۲. درختان داخل Zone رو بگیر
        cur.execute(queries_zones.get_features_in_zone_query(zone_id), (zone_id,))
        rows = cur.fetchall()
        cur.close()
        
        features = [
            {
                "feature_id": r[0],
                "type_code": r[1],
                "icon": r[2],
                "color": r[3],
                "lon": r[4],
                "lat": r[5],
                "last_updated": r[6].isoformat() if r[6] else None,
                "attributes": r[7] or {}
            }
            for r in rows
        ]
        
        return {
            "zone": zone_info,
            "total_count": len(features),
            "features": features
        }
    finally:
        return_connection(conn)

@router.get("", response_model=List[Zone])
def list_zones():
    """لیست همه Zoneها"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(queries_zones.get_all_zones_query())
        rows = cur.fetchall()
        cur.close()
        return [
            Zone(
                zone_id=r[0],
                name=r[1],
                description=r[2],
                polygon=r[3],
                filters=r[4],
                rules=r[5],
                is_active=r[6],
                created_at=r[7],
                updated_at=r[8]
            )
            for r in rows
        ]
    finally:
        return_connection(conn)


@router.get("/{zone_id}", response_model=Zone)
def get_zone(zone_id: str):
    """جزئیات یه Zone"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(queries_zones.get_zone_by_id_query(), (zone_id,))
        r = cur.fetchone()
        cur.close()
        if not r:
            raise HTTPException(status_code=404, detail="Zone not found")
        return Zone(
            zone_id=r[0],
            name=r[1],
            description=r[2],
            polygon=r[3],
            filters=r[4],
            rules=r[5],
            is_active=r[6],
            created_at=r[7],
            updated_at=r[8]
        )
    finally:
        return_connection(conn)


@router.post("", response_model=Zone)
def create_zone(zone: ZoneCreate):
    """ساخت Zone جدید"""
    conn = get_connection()
    try:
        cur = conn.cursor()

        # تبدیل GeoJSON به string
        polygon_geojson = json.dumps(zone.polygon)
        filters_json = json.dumps(zone.filters) if zone.filters else None
        rules_json = json.dumps(zone.rules) if zone.rules else None

        cur.execute(
            queries_zones.create_zone_query(),
            (zone.name, zone.description, polygon_geojson, filters_json, rules_json)
        )
        new_zone_id = cur.fetchone()[0]
        conn.commit()
        cur.close()

        # برگردون Zone جدید
        cur = conn.cursor()
        cur.execute(queries_zones.get_zone_by_id_query(), (new_zone_id,))
        r = cur.fetchone()
        cur.close()

        return Zone(
            zone_id=r[0], name=r[1], description=r[2],
            polygon=r[3], filters=r[4], rules=r[5],
            is_active=r[6], created_at=r[7], updated_at=r[8]
        )
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        return_connection(conn)


@router.put("/{zone_id}", response_model=Zone)
def update_zone(zone_id: str, zone: ZoneUpdate):
    """آپدیت Zone"""
    conn = get_connection()
    try:
        cur = conn.cursor()

        polygon_geojson = json.dumps(zone.polygon) if zone.polygon else None
        filters_json = json.dumps(zone.filters) if zone.filters else None
        rules_json = json.dumps(zone.rules) if zone.rules else None

        cur.execute(
            queries_zones.update_zone_query(),
            (
                zone.name, zone.description,
                polygon_geojson, filters_json, rules_json,
                zone.is_active, zone_id
            )
        )
        result = cur.fetchone()
        conn.commit()
        cur.close()

        if not result:
            raise HTTPException(status_code=404, detail="Zone not found")

        # برگردون Zone آپدیت‌شده
        cur = conn.cursor()
        cur.execute(queries_zones.get_zone_by_id_query(), (zone_id,))
        r = cur.fetchone()
        cur.close()

        return Zone(
            zone_id=r[0], name=r[1], description=r[2],
            polygon=r[3], filters=r[4], rules=r[5],
            is_active=r[6], created_at=r[7], updated_at=r[8]
        )
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        return_connection(conn)


@router.delete("/{zone_id}")
def delete_zone(zone_id: str):
    """حذف Zone"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(queries_zones.delete_zone_query(), (zone_id,))
        result = cur.fetchone()
        conn.commit()
        cur.close()
        if not result:
            raise HTTPException(status_code=404, detail="Zone not found")
        return {"message": "Zone deleted", "zone_id": result[0]}
    finally:
        return_connection(conn)


@router.get("/{zone_id}/scene")
def get_zone_scene(zone_id: str):
    """
    برای Unreal: داده‌های یه Zone رو برمی‌گردونه
    """
    conn = get_connection()
    try:
        # ۱. Zone رو بگیر
        cur = conn.cursor()
        cur.execute(queries_zones.get_zone_by_id_query(), (zone_id,))
        zone_row = cur.fetchone()
        if not zone_row:
            cur.close()
            raise HTTPException(status_code=404, detail="Zone not found")

        zone_info = {
            "zone_id": zone_row[0],
            "name": zone_row[1],
            "description": zone_row[2],
            "filters": zone_row[4],
            "rules": zone_row[5]
        }

        # ۲. داده‌های داخل پلیگون رو بگیر
        cur.execute(queries_zones.get_features_in_zone_query(zone_id), (zone_id,))
        rows = cur.fetchall()
        cur.close()

        features = [
            {
                "feature_id": r[0],
                "type_code": r[1],
                "icon": r[2],
                "color": r[3],
                "lon": r[4],
                "lat": r[5],
                "last_updated": r[6].isoformat() if r[6] else None,
                "attributes": r[7] or {}
            }
            for r in rows
        ]

        return {
            "zone": zone_info,
            "total_count": len(features),
            "features": features
        }
    finally:
        return_connection(conn)
@router.put("/{zone_id}/activate")
def activate_zone(zone_id: str):
    """فعال کردن یه Zone (بقیه غیرفعال می‌شن)"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # ۱. اول همه رو غیرفعال کن
        cur.execute(queries_zones.deactivate_all_zones_query())
        
        # ۲. بعد این یکی رو فعال کن
        cur.execute(queries_zones.activate_zone_query(), (zone_id,))
        result = cur.fetchone()
        
        if not result:
            conn.rollback()
            cur.close()
            raise HTTPException(status_code=404, detail="Zone not found")
        
        conn.commit()
        cur.close()
        
        return {
            "message": "Zone activated",
            "zone_id": result[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        return_connection(conn)


