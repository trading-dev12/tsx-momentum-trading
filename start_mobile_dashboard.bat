@echo off
cd /d "C:\Users\Chris\Documents\Tsx momentum trading\tsx-momentum-trading"
python -m waitress --listen=127.0.0.1:5000 mobile_dashboard.app:app
pause