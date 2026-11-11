# ============================================
# API Configuration
# ============================================

# Database
DB_HOST = "localhost"
DB_NAME = "trees_berlin"
DB_USER = "postgres"
DB_POOL_MIN = 1
DB_POOL_MAX = 10

# API
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000

# CRS
# SRID دیتابیس (UTM 33N)
SOURCE_SRID = 25833
# SRID خروجی API (WGS84)
OUTPUT_SRID = 4326

# Bounding Box
# محدوده پیش‌فرض برلین (اگه Bounding Box داده نشه)
DEFAULT_BBOX = {
    "min_lon": 13.0,
    "max_lon": 13.8,
    "min_lat": 52.3,
    "max_lat": 52.7
}

# فقط درخت‌های این محدوده رو برگردون (اختیاری)
ENFORCE_BBOX = False  # اگه True بشه، همیشه Bounding Box الزامی می‌شه