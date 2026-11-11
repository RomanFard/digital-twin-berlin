from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

from database import get_connection, return_connection
from schemas import Tree, SyncStatus
from config import DEFAULT_LIMIT, MAX_LIMIT
import queries
import routes_features
import dashboard
import routes_zones
import routes_rules
app = FastAPI(title="Trees Berlin API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# اضافه کردن router جدید
app.include_router(routes_features.router)
app.include_router(dashboard.router)
app.include_router(routes_zones.router)
app.include_router(routes_rules.router)

@app.get("/")
def root():
    return {"message": "Trees Berlin API v2", "docs": "/docs"}


@app.get("/health")
def health():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(queries.get_trees_count_query())
        count = cur.fetchone()[0]
        cur.close()
        return {"status": "ok", "trees_count": count}
    finally:
        return_connection(conn)


@app.get("/trees", response_model=List[Tree])
def get_trees(
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    min_lon: Optional[float] = Query(None),
    max_lon: Optional[float] = Query(None),
    min_lat: Optional[float] = Query(None),
    max_lat: Optional[float] = Query(None)
):
    bbox = None
    if all(v is not None for v in [min_lon, max_lon, min_lat, max_lat]):
        bbox = {"min_lon": min_lon, "max_lon": max_lon,
                "min_lat": min_lat, "max_lat": max_lat}

    query, params = queries.get_trees_query(bbox)
    params.extend([limit, offset])

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        return [
            Tree(
                tree_id=r[0], lon=r[1], lat=r[2],
                art_dtsch=r[3], art_bot=r[4], stammumfg=r[5],
                baumhoehe=r[6], kronedurch=r[7], pflanzjahr=r[8],
                bezirk=r[9], last_updated=r[10]
            )
            for r in rows
        ]
    finally:
        return_connection(conn)


@app.get("/trees/{tree_id}", response_model=Tree)
def get_tree(tree_id: str):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(queries.get_tree_by_id_query(), (tree_id,))
        r = cur.fetchone()
        cur.close()
        if not r:
            raise HTTPException(status_code=404, detail="Tree not found")
        return Tree(
            tree_id=r[0], lon=r[1], lat=r[2],
            art_dtsch=r[3], art_bot=r[4], stammumfg=r[5],
            baumhoehe=r[6], kronedurch=r[7], pflanzjahr=r[8],
            bezirk=r[9], last_updated=r[10]
        )
    finally:
        return_connection(conn)


@app.get("/sync/status", response_model=SyncStatus)
def get_sync_status():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(queries.get_sync_status_query())
        r = cur.fetchone()
        cur.close()
        if not r:
            raise HTTPException(status_code=404, detail="No sync found")
        return SyncStatus(
            sync_batch_id=str(r[0]),
            started_at=r[1], finished_at=r[2],
            records_read=r[3], records_inserted=r[4],
            records_updated=r[5], records_deleted=r[6],
            status=r[7]
        )
    finally:
        return_connection(conn)