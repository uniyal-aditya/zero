# config.py
import os

BOT_NAME    = os.getenv("BOT_NAME", "Zero")
PREFIX      = os.getenv("PREFIX", ".")
DB_PATH     = os.getenv("DB_PATH", "zero.db")
MAX_VOLUME  = int(os.getenv("MAX_VOLUME", "200"))
