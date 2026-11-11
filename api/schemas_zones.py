from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class ZoneCreate(BaseModel):
    name: str
    description: Optional[str] = None
    polygon: Dict[str, Any]
    filters: Optional[Dict[str, Any]] = None
    rules: Optional[Dict[str, Any]] = None


class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    polygon: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    rules: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class Zone(BaseModel):
    zone_id: str
    name: str
    description: Optional[str] = None
    polygon: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    rules: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None