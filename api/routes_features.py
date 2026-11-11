from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from database import get_connection, return_connection
from schemas_features import Feature, FeatureType, SceneResponse, StatsResponse
import queries_features
from pydantic import BaseModel
from typing import Dict, Any

class PolygonRequest(BaseModel):
    polygon: Dict[str, Any]
    types: str = None
    limit: int = 50000
    offset: int = 0

router = APIRouter(prefix="/api", tags=["features"])


@router.get("/layers", response_model=List[FeatureType])
def get_layers():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(queries_features.get_all_types_query())
        rows = cur.fetchall()
        cur.close()
        return [
            FeatureType(
                id=r[0], code=r[1], name_fa=r[2], name_en=r[3],
                name_de=r[4], icon=r[5], color=r[6],
                geometry_type=r[7], source_url=r[8]
            )
            for r in rows
        ]
    finally:
        return_connection(conn)


@router.get("/features", response_model=List[Feature])
def get_features(
    types: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    strname: Optional[str] = Query(None),
):
    type_codes = types.split(",") if types else None
    bbox = None
    if all(v is not None for v in [min_lon, max_lon, min_lat, max_lat]):
        bbox = {"min_lon": min_lon, "max_lon": max_lon,
                "min_lat": min_lat, "max_lat": max_lat}

    query, params = queries_features.get_features_query(type_codes, bbox, strname)
    params.extend([limit, offset])

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        return [
            Feature(
                feature_id=r[0], type_code=r[1], icon=r[2], color=r[3],
                lon=r[4], lat=r[5], last_updated=r[6],
                attributes=r[7] or {}
            )
            for r in rows
        ]
    finally:
        return_connection(conn)


@router.get("/features/{feature_id}", response_model=Feature)
def get_feature(feature_id: str):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(queries_features.get_feature_by_id_query(), (feature_id,))
        r = cur.fetchone()
        cur.close()
        if not r:
            raise HTTPException(status_code=404, detail="Feature not found")
        return Feature(
            feature_id=r[0], type_code=r[1], icon=r[2], color=r[3],
            lon=r[4], lat=r[5], last_updated=r[6],
            attributes=r[7] or {}
        )
    finally:
        return_connection(conn)


@router.get("/scene", response_model=SceneResponse)
def get_scene(
    types: Optional[str] = Query(None),
    limit: int = Query(1000, ge=1, le=100000),
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
):
    type_codes = types.split(",") if types else None
    bbox = None
    if all(v is not None for v in [min_lon, max_lon, min_lat, max_lat]):
        bbox = {"min_lon": min_lon, "max_lon": max_lon,
                "min_lat": min_lat, "max_lat": max_lat}

    query, params = queries_features.get_scene_query(type_codes, bbox)
    params.extend([limit, 0])

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()

        features = [
            Feature(
                feature_id=r[0], type_code=r[1], icon=r[2], color=r[3],
                lon=r[4], lat=r[5], last_updated=r[6],
                attributes=r[7] or {}
            )
            for r in rows
        ]

        return SceneResponse(
            data_version=None,
            sync_batch_id=None,
            bbox=[min_lon, min_lat, max_lon, max_lat] if bbox else None,
            total_count=len(features),
            features=features
        )
    finally:
        return_connection(conn)


@router.get("/stats", response_model=List[StatsResponse])
def get_stats():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(queries_features.get_stats_query())
        rows = cur.fetchall()
        cur.close()
        return [
            StatsResponse(
                type_code=r[0], total=r[6], active=r[4], deleted=r[5]
            )
            for r in rows
        ]
    finally:
        return_connection(conn)


@router.get("/stats/bezirk")
def get_stats_bezirk(type_code: str = Query("tree")):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(queries_features.get_count_by_bezirk_query(type_code), (type_code,))
        rows = cur.fetchall()
        cur.close()
        return [{"bezirk": r[0], "count": r[1]} for r in rows]
    finally:
        return_connection(conn)
@router.post("/features/in-polygon", response_model=List[Feature])
def get_features_in_polygon(request: PolygonRequest):
    """
    Get features inside a GeoJSON polygon
    """
    from shapely.geometry import shape
    from shapely import wkt as shapely_wkt

    # تبدیل GeoJSON به WKT
    try:
        geom = shape(request.polygon)
        polygon_wkt = geom.wkt
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid polygon: {str(e)}")

    type_codes = request.types.split(",") if request.types else None

    query, params = queries_features.get_features_in_polygon_query(
        polygon_wkt, type_codes, request.limit, request.offset
    )

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        return [
            Feature(
                feature_id=r[0], type_code=r[1], icon=r[2], color=r[3],
                lon=r[4], lat=r[5], last_updated=r[6],
                attributes=r[7] or {}
            )
            for r in rows
        ]
    finally:
        return_connection(conn)
