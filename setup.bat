@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Project Manager Setup
python setup.py
pause
