@echo off
echo ========================================
echo   Importing data to PostgreSQL
echo ========================================
echo.

echo [1/3] Importing Park Trees...
"C:\Program Files\QGIS 4.2.1\bin\ogr2ogr.exe" -f PostgreSQL "PG:host=localhost user=postgres dbname=trees_berlin" "C:\Users\Roman\Documents\code\data\baumbestand_full.gpkg" baumbestand:anlagenbaeume -nln trees_raw -lco GEOMETRY_NAME=geom -overwrite

echo.
echo [2/3] Importing Street Trees...
"C:\Program Files\QGIS 4.2.1\bin\ogr2ogr.exe" -f PostgreSQL "PG:host=localhost user=postgres dbname=trees_berlin" "C:\Users\Roman\Documents\code\data\strassenbaeume_full.gpkg" strassenbaeume -nln street_trees_raw -lco GEOMETRY_NAME=geom -overwrite

echo.
echo [3/3] Done!
pause