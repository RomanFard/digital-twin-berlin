import subprocess
import os
import sys
from datetime import datetime

# ============================================
# Config
# ============================================
OGR2OGR = r"C:\Program Files\QGIS 4.2.1\bin\ogr2ogr.exe"
WFS_URL = "WFS:https://gdi.berlin.de/services/wfs/baumbestand?service=WFS&version=2.0.0"
LAYER = "baumbestand:anlagenbaeume"
OUTPUT_DIR = r"C:\Users\Roman\Documents\code\data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "baumbestand_latest.gpkg")

# ============================================
# Main
# ============================================
def main():
    # ساخت پوشه اگه نیست
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # پاک کردن فایل قبلی
    if os.path.exists(OUTPUT_FILE):
        print(f"Removing old file: {OUTPUT_FILE}")
        os.remove(OUTPUT_FILE)
    
    print(f"[{datetime.now()}] Starting download from WFS...")
    print(f"Output: {OUTPUT_FILE}")
    
    cmd = [
        OGR2OGR,
        "-f", "GPKG",
        OUTPUT_FILE,
        WFS_URL,
        LAYER,
        "--config", "OGR_WFS_PAGE_SIZE", "10000",
        "--config", "OGR_WFS_PAGING_ALLOWED", "ON"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("ERROR during download:")
        print(result.stderr)
        sys.exit(1)
    
    # چک کنیم فایل ساخته شده
    if not os.path.exists(OUTPUT_FILE):
        print("ERROR: Output file not created!")
        sys.exit(1)
    
    size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"[{datetime.now()}] Download complete: {size_mb:.1f} MB")
    
    # چک تعداد رکورد
    ogrinfo = OGR2OGR.replace("ogr2ogr.exe", "ogrinfo.exe")
    result = subprocess.run(
        [ogrinfo, "-al", "-so", OUTPUT_FILE],
        capture_output=True, text=True
    )
    
    # پیدا کردن Feature Count
    for line in result.stdout.split("\n"):
        if "Feature Count" in line:
            print(f"  {line.strip()}")
            break

if __name__ == "__main__":
    main()