@echo off
set PYYAML_FORCE_LIBYAML=0
call "%~dp0start_redis.bat"
echo Starting Mount Fuji Backend Server...
echo Server : http://localhost:8001
echo Swagger: http://localhost:8001/docs
uv run uvicorn src.connection.socket:main_server --reload --host 0.0.0.0 --port 8001
