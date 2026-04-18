@echo off
cd /d %~dp0
C:\Users\greyrofl\AppData\Local\Python\bin\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000