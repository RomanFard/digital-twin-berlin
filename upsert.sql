-- ============================================
-- UPSERT Script for trees_berlin (INSERT + UPDATE + SOFT DELETE)
-- ============================================

BEGIN;

-- 1. ایجاد sync_batch_id جدید
CREATE TEMP TABLE batch_info AS
SELECT gen_random_uuid() AS sync_batch_id;

-- 2. ثبت در sync_log
INSERT INTO sync_log (sync_batch_id, source, status)
SELECT sync_batch_id, 'WFS_Berlin_Baumbestand', 'running'
FROM batch_info;

-- 3. آرشیو رکوردهای تغییرکرده در trees_history
INSERT INTO trees_history (pitid, version, valid_from, valid_to, row_hash, sync_batch_id, data)
SELECT 
    c.tree_id,
    COALESCE((SELECT MAX(version) FROM trees_history h WHERE h.pitid = c.tree_id), 0) + 1,
    c.last_updated,
    NOW(),
    c.row_hash,
    b.sync_batch_id,
    to_jsonb(c.*)
FROM trees_current c
CROSS JOIN batch_info b
INNER JOIN trees_raw r ON COALESCE(NULLIF(r.pitid, ''), r.gisid) = c.tree_id
WHERE c.deleted_at IS NULL
  AND c.row_hash IS DISTINCT FROM MD5(
    COALESCE(c.tree_id,'') || '|' || 
    COALESCE(r.art_dtsch,'') || '|' || 
    COALESCE(r.art_bot,'') || '|' || 
    COALESCE(r.stammumfg::text,'') || '|' || 
    COALESCE(r.baumhoehe::text,'') || '|' || 
    COALESCE(r.kronedurch::text,'') || '|' || 
    COALESCE(r.standalter::text,'') || '|' || 
    COALESCE(ST_AsText(r.geom),'')
);

-- 4. آپدیت رکوردهای تغییرکرده
UPDATE trees_current c
SET 
    art_dtsch = r.art_dtsch,
    art_bot = r.art_bot,
    gattung_deutsch = r.gattung_deutsch,
    gattung = r.gattung,
    art_gruppe = r.art_gruppe,
    pflanzjahr = r.pflanzjahr,
    standalter = r.standalter,
    kronedurch = r.kronedurch,
    stammumfg = r.stammumfg,
    baumhoehe = r.baumhoehe,
    eigentuemer = r.eigentuemer,
    bezirk = r.bezirk,
    geom = r.geom,
    row_hash = MD5(
        COALESCE(c.tree_id,'') || '|' || 
        COALESCE(r.art_dtsch,'') || '|' || 
        COALESCE(r.art_bot,'') || '|' || 
        COALESCE(r.stammumfg::text,'') || '|' || 
        COALESCE(r.baumhoehe::text,'') || '|' || 
        COALESCE(r.kronedurch::text,'') || '|' || 
        COALESCE(r.standalter::text,'') || '|' || 
        COALESCE(ST_AsText(r.geom),'')
    ),
    sync_batch_id = (SELECT sync_batch_id FROM batch_info),
    last_updated = NOW(),
    deleted_at = NULL
FROM trees_raw r
WHERE COALESCE(NULLIF(r.pitid, ''), r.gisid) = c.tree_id
  AND c.deleted_at IS NULL
  AND c.row_hash IS DISTINCT FROM MD5(
        COALESCE(c.tree_id,'') || '|' || 
        COALESCE(r.art_dtsch,'') || '|' || 
        COALESCE(r.art_bot,'') || '|' || 
        COALESCE(r.stammumfg::text,'') || '|' || 
        COALESCE(r.baumhoehe::text,'') || '|' || 
        COALESCE(r.kronedurch::text,'') || '|' || 
        COALESCE(r.standalter::text,'') || '|' || 
        COALESCE(ST_AsText(r.geom),'')
    );

-- 5. INSERT رکوردهای جدید
INSERT INTO trees_current (tree_id, pitid, gisid, standortnr, kennzeich, namenr, art_dtsch, art_bot, gattung_deutsch, gattung, art_gruppe, pflanzjahr, standalter, kronedurch, stammumfg, baumhoehe, eigentuemer, bezirk, geom, row_hash, sync_batch_id, deleted_at)
SELECT 
    COALESCE(NULLIF(r.pitid, ''), r.gisid),
    r.pitid,
    r.gisid,
    r.standortnr,
    r.kennzeich,
    r.namenr,
    r.art_dtsch,
    r.art_bot,
    r.gattung_deutsch,
    r.gattung,
    r.art_gruppe,
    r.pflanzjahr,
    r.standalter,
    r.kronedurch,
    r.stammumfg,
    r.baumhoehe,
    r.eigentuemer,
    r.bezirk,
    r.geom,
    MD5(
        COALESCE(COALESCE(NULLIF(r.pitid, ''), r.gisid),'') || '|' || 
        COALESCE(r.art_dtsch,'') || '|' || 
        COALESCE(r.art_bot,'') || '|' || 
        COALESCE(r.stammumfg::text,'') || '|' || 
        COALESCE(r.baumhoehe::text,'') || '|' || 
        COALESCE(r.kronedurch::text,'') || '|' || 
        COALESCE(r.standalter::text,'') || '|' || 
        COALESCE(ST_AsText(r.geom),'')
    ),
    (SELECT sync_batch_id FROM batch_info),
    NULL
FROM trees_raw r
LEFT JOIN trees_current c ON COALESCE(NULLIF(r.pitid, ''), r.gisid) = c.tree_id
WHERE c.tree_id IS NULL;

-- 6. SOFT DELETE رکوردهایی که تو raw نیستن
UPDATE trees_current c
SET 
    deleted_at = NOW(),
    sync_batch_id = (SELECT sync_batch_id FROM batch_info),
    last_updated = NOW()
WHERE c.deleted_at IS NULL
  AND NOT EXISTS (
    SELECT 1 FROM trees_raw r 
    WHERE COALESCE(NULLIF(r.pitid, ''), r.gisid) = c.tree_id
  );

-- 7. آپدیت لاگ
UPDATE sync_log
SET 
    finished_at = NOW(),
    records_read = (SELECT COUNT(*) FROM trees_raw),
    records_deleted = (SELECT COUNT(*) FROM trees_current WHERE deleted_at IS NOT NULL AND sync_batch_id = (SELECT sync_batch_id FROM batch_info)),
    status = 'completed'
WHERE sync_batch_id = (SELECT sync_batch_id FROM batch_info);

COMMIT;