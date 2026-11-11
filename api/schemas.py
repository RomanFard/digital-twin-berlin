from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Tree(BaseModel):
    tree_id: str
    lon: float
    lat: float
    art_dtsch: Optional[str] = None
    art_bot: Optional[str] = None
    stammumfg: Optional[int] = None
    baumhoehe: Optional[float] = None
    kronedurch: Optional[float] = None
    pflanzjahr: Optional[str] = None
    bezirk: Optional[str] = None
    last_updated: Optional[datetime] = None

class SyncStatus(BaseModel):
    sync_batch_id: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    records_read: Optional[int] = None
    records_inserted: Optional[int] = None
    records_updated: Optional[int] = None
    records_deleted: Optional[int] = None
    status: Optional[str] = None