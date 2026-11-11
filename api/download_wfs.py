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
OUTPUT_DIR = r"C:\Users\Roman\Documents\code\data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "baumbestand_latest.gpkg")
EXPECTED_SIZE_MB = 162
SHUTDOWN_AFTER_DONE = True   # ← اگه True باشه، بعد از دانلود سیستم خاموش می‌شه
SHUTDOWN_DELAY_SEC = 60      # ← ۶۰ ثانیه فرصت برای لغو

# ============================================
# Main
# ============================================
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
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
    
    # اجرای ogr2ogr به صورت non-blocking
    process = subprocess.Popen(cmd)
    
    # هر ۶۰ ثانیه حجم فایل رو چک کن و پیشرفت رو نشون بده
    while process.poll() is None:
        time.sleep(60)
        if os.path.exists(OUTPUT_FILE):
            size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
            pct = (size_mb / EXPECTED_SIZE_MB) * 100
            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                  f"{size_mb:.1f} MB / {EXPECTED_SIZE_MB} MB "
                  f"({pct:.1f}%)")
    
    # نتیجه
    if process.returncode != 0:
        print(f"[{datetime.now()}] ERROR: ogr2ogr exited with code {process.returncode}")
        sys.exit(1)
    
    if not os.path.exists(OUTPUT_FILE):
        print(f"[{datetime.now()}] ERROR: Output file not created!")
        sys.exit(1)
    
    size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"[{datetime.now()}] DONE: {size_mb:.1f} MB")
    
    # ============================================
    # Shutdown
    # ============================================
    if SHUTDOWN_AFTER_DONE:
        print(f"\n{'='*50}")
        print(f"System will shutdown in {SHUTDOWN_DELAY_SEC} seconds...")
        print(f"Run 'shutdown /a' to cancel.")
        print(f"{'='*50}\n")
        os.system(f"shutdown /s /t {SHUTDOWN_DELAY_SEC}")

if __name__ == "__main__":
    main()