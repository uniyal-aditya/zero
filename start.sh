#!/bin/bash
# Zero Music Bot - Startup Script
# Forces correct package versions on every start

echo "=== Zero Music Bot ==="
echo "Checking dependencies..."

# Force install correct versions (clears any cached wrong versions)
pip install --quiet --force-reinstall \
    "discord.py==2.4.0" \
    "wavelink==3.4.1" \
    "python-dotenv==1.0.0" \
    "aiohttp==3.10.5" \
    "psutil==5.9.8"

echo "Dependencies ready. Starting bot..."
python bot.py
