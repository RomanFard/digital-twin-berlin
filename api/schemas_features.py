from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class FeatureType(BaseModel):
    id: int
    code: str
    name_fa: Optional[str] = None
    name_en: Optional[str] = None
    name_de: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    geometry_type: Optional[str] = None
    source_url: Optional[str] = None

class Feature(BaseModel):
    feature_id: str
    type_code: str
    lon: float
    lat: float
    icon: Optional[str] = None
    color: Optional[str] = None
    attributes: Dict[str, Any] = {}
    last_updated: Optional[datetime] = None

class SceneResponse(BaseModel):
    data_version: Optional[str] = None
    sync_batch_id: Optional[str] = None
    bbox: Optional[List[float]] = None
    total_count: int
    features: List[Feature]

class StatsResponse(BaseModel):
    type_code: str
    total: int
    deleted: int
    active: int
    by_bezirk: Optional[Dict[str, int]] = None