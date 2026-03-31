@echo off
echo === JODETTU Market Bulk Upload Fix ===
echo.
echo This script bypasses Swagger UI issues by using curl directly
echo.

set /p csv_path="Enter path to CSV file: "
set /p img_path="Enter path to image file (or press Enter if none): "

echo.
echo Testing with Market bulk upload...

if "%img_path%"=="" (
    echo Uploading CSV only...
    curl -X POST "http://202.21.38.161:9090/Jodettu/Market/bulk-upload" ^
      -H "accept: application/json" ^
      -H "Authorization: Bearer eyJhb6ciOiJIUzI1NiIsInR5cCI6IkpXVC39.eyJzdWIiOiIrOTE4MDUwNzMzNTYzIiwidXNlcl9pZCI6I1VTRVJfMDAwMiIsInJvbGU" ^
      -H "Content-Type: multipart/form-data" ^
      -F "csv_file=@%csv_path%;type=text/csv"
) else (
    echo Uploading CSV + image...
    curl -X POST "http://202.21.38.161:9090/Jodettu/Market/bulk-upload" ^
      -H "accept: application/json" ^
      -H "Authorization: Bearer eyJhb6ciOiJIUzI1NiIsInR5cCI6IkpXVC39.eyJzdWIiOiIrOTE4MDUwNzMzNTYzIiwidXNlcl9pZCI6I1VTRVJfMDAwMiIsInJvbGU" ^
      -H "Content-Type: multipart/form-data" ^
      -F "csv_file=@%csv_path%;type=text/csv" ^
      -F "files=@%img_path%"
)

echo.
echo === Done ===
pause
