
@echo off
echo Esperando liberacion de archivos...
timeout /t 2 /nobreak > nul
if exist "D:/colegio_vaca_diez/instance/colegio_vaca_diez.db-wal" del "D:/colegio_vaca_diez/instance/colegio_vaca_diez.db-wal"
if exist "D:/colegio_vaca_diez/instance/colegio_vaca_diez.db-shm" del "D:/colegio_vaca_diez/instance/colegio_vaca_diez.db-shm"
echo Reiniciando servidor...
cd /d "D:\colegio_vaca_diez"
python app.py
del "%~f0"
