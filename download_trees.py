import subprocess
import os
import time

OGR2OGR = r"C:\Program Files\QGIS 4.2.1\bin\ogr2ogr.exe"
WFS_URL = 'WFS:"https://gdi.berlin.de/services/wfs/baumbestand?service=WFS&request=GetCapabilities&version=2.0.0"'
LAYER = "baumbestand:anlagenbaeume"
OUTPUT = r"C:\Users\Roman\Documents\code\baumbestand_full.gpkg"
CHUNK = 10000
TOTAL = 527780

if os.path.exists(OUTPUT):
    os.remove(OUTPUT)

start = 0
chunk_num = 0

while start < TOTAL:
    chunk_num += 1
    print(f"\n=== Chunk {chunk_num}: startIndex={start} ===")
    
    cmd = [
        OGR2OGR,
        "--config", "OGR_WFS_PAGE_SIZE", str(CHUNK),
        "--config", "OGR_WFS_BASE_START_INDEX", str(start),
        "--config", "OGR_WFS_PAGING_ALLOWED", "YES",
        "-f", "GPKG",
        OUTPUT,
        WFS_URL,
        LAYER
    ]
    
    if start > 0:
        cmd.insert(1, "-append")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"ERROR in chunk {chunk_num}:")
        print(result.stderr)
        print("Stopping. Fix and rerun.")
        break
    
    print(f"OK: chunk {chunk_num} done")
    start += CHUNK
    time.sleep(1)

print("\n=== DONE ===")