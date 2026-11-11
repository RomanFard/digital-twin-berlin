import subprocess
import os
import sys
import time
from datetime import datetime

OGR2OGR = r"C:\Program Files\QGIS 4.2.1\bin\ogr2ogr.exe"
WFS_URL = "WFS:https://gdi.berlin.de/services/wfs/baumbestand?service=WFS&version=2.0.0"
LAYER = "baumbestand:strassenbaeume"
OUTPUT_DIR = r"C:\Users\Roman\Documents\code\data\chunks_street"
FINAL_OUTPUT = r"C:\Users\Roman\Documents\code\data\strassenbaeume_full.gpkg"
CHUNK_SIZE = 50000
TOTAL_RECORDS = 434765
SHUTDOWN_AFTER_DONE = False
SHUTDOWN_DELAY_SEC = 60


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    total_chunks = (TOTAL_RECORDS + CHUNK_SIZE - 1) // CHUNK_SIZE
    print(f"[{datetime.now()}] Total chunks: {total_chunks} (each {CHUNK_SIZE} records)")

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
            sys.exit(1)

        if os.path.exists(chunk_file):
            size_mb = os.path.getsize(chunk_file) / (1024*1024)
            print(f"  OK: Chunk {i+1} done ({size_mb:.1f} MB)")
        else:
            print(f"  WARNING: Chunk {i+1} file not created!")
            sys.exit(1)

    print(f"\n[{datetime.now()}] Merging chunks...")

    if os.path.exists(FINAL_OUTPUT):
        os.remove(FINAL_OUTPUT)

    first_chunk = os.path.join(OUTPUT_DIR, "chunk_000.gpkg")
    subprocess.run([OGR2OGR, "-f", "GPKG", FINAL_OUTPUT, first_chunk], check=True)

    for i in range(1, total_chunks):
        chunk_file = os.path.join(OUTPUT_DIR, f"chunk_{i:03d}.gpkg")
        print(f"Appending chunk {i+1}/{total_chunks}...")
        subprocess.run([OGR2OGR, "-f", "GPKG", "-append", FINAL_OUTPUT, chunk_file], check=True)

    final_size = os.path.getsize(FINAL_OUTPUT) / (1024*1024)
    print(f"\n[{datetime.now()}] DONE: {final_size:.1f} MB")

    if SHUTDOWN_AFTER_DONE:
        print(f"\nSystem will shutdown in {SHUTDOWN_DELAY_SEC} seconds...")
        print("Run 'shutdown /a' to cancel.")
        os.system(f"shutdown /s /t {SHUTDOWN_DELAY_SEC}")


if __name__ == "__main__":
    main()