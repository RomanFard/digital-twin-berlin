import subprocess
import os
import sys
import time
from datetime import datetime

# ============================================
# Config
# ============================================
OGR2OGR = r"C:\Program Files\QGIS 4.2.1\bin\ogr2ogr.exe"
WFS_URL = "WFS:https://gdi.berlin.de/services/wfs/baumbestand?service=WFS&version=2.0.0"
LAYER = "baumbestand:anlagenbaeume"
OUTPUT_DIR = r"C:\Users\Roman\Documents\code\data\chunks"
FINAL_OUTPUT = r"C:\Users\Roman\Documents\code\data\baumbestand_full.gpkg"
CHUNK_SIZE = 50000
TOTAL_RECORDS = 527780
SHUTDOWN_AFTER_DONE = True
SHUTDOWN_DELAY_SEC = 60

# ============================================
# Main
# ============================================
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    total_chunks = (TOTAL_RECORDS + CHUNK_SIZE - 1) // CHUNK_SIZE
    print(f"[{datetime.now()}] Total chunks: {total_chunks} (each {CHUNK_SIZE} records)")
    
    # دانلود chunkها
    for i in range(total_chunks):
        start = i * CHUNK_SIZE
        chunk_file = os.path.join(OUTPUT_DIR, f"chunk_{i:03d}.gpkg")
        
        if os.path.exists(chunk_file):
            size_mb = os.path.getsize(chunk_file) / (1024*1024)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Chunk {i+1}/{total_chunks} exists ({size_mb:.1f} MB), skipping")
            continue
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Downloading chunk {i+1}/{total_chunks} (startIndex={start})...")
        
        cmd = [
            OGR2OGR,
            "-f", "GPKG",
            chunk_file,
            WFS_URL,
            LAYER,
            "--config", "OGR_WFS_PAGE_SIZE", "10000",
            "--config", "OGR_WFS_BASE_START_INDEX", str(start),
            "--config", "OGR_WFS_PAGING_ALLOWED", "ON",
            "-limit", str(CHUNK_SIZE)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"ERROR in chunk {i+1}:")
            print(result.stderr)
            print("Stopping. Re-run to resume.")
            sys.exit(1)
        
        if os.path.exists(chunk_file):
            size_mb = os.path.getsize(chunk_file) / (1024*1024)
            print(f"  ✓ Chunk {i+1} done ({size_mb:.1f} MB)")
        else:
            print(f"  ⚠ Chunk {i+1} file not created!")
            sys.exit(1)
    
    # Merge کردن chunkها
    print(f"\n[{datetime.now()}] All {total_chunks} chunks downloaded. Merging...")
    
    if os.path.exists(FINAL_OUTPUT):
        print(f"Removing old final file: {FINAL_OUTPUT}")
        os.remove(FINAL_OUTPUT)
    
    # اولین chunk رو کپی کن
    first_chunk = os.path.join(OUTPUT_DIR, "chunk_000.gpkg")
    print(f"Copying chunk 1...")
    cmd = [OGR2OGR, "-f", "GPKG", FINAL_OUTPUT, first_chunk]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("ERROR during merge (first chunk):")
        print(result.stderr)
        sys.exit(1)
    
    # بقیه رو append کن
    for i in range(1, total_chunks):
        chunk_file = os.path.join(OUTPUT_DIR, f"chunk_{i:03d}.gpkg")
        print(f"Appending chunk {i+1}/{total_chunks}...")
        cmd = [OGR2OGR, "-f", "GPKG", "-append", FINAL_OUTPUT, chunk_file]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ERROR merging chunk {i+1}:")
            print(result.stderr)
            sys.exit(1)
    
    final_size = os.path.getsize(FINAL_OUTPUT) / (1024*1024)
    print(f"\n[{datetime.now()}] ✓ DONE: {final_size:.1f} MB")
    
    # Shutdown
    if SHUTDOWN_AFTER_DONE:
        print(f"\n{'='*50}")
        print(f"System will shutdown in {SHUTDOWN_DELAY_SEC} seconds...")
        print(f"Run 'shutdown /a' to cancel.")
        print(f"{'='*50}\n")
        os.system(f"shutdown /s /t {SHUTDOWN_DELAY_SEC}")

if __name__ == "__main__":
    main()