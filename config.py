# config.py
import os

BOT_NAME = os.getenv("BOT_NAME", "Zero™")
PREFIX = os.getenv("PREFIX", ".")
DB_PATH = os.getenv("DB_PATH", "zero.db")
MAX_VOLUME = int(os.getenv("MAX_VOLUME", "200"))

# Lavalink defaults (can be overriden via env)
LAVALINK_HOST = os.getenv("LAVALINK_HOST", "127.0.0.1")
LAVALINK_PORT = int(os.getenv("LAVALINK_PORT", "2333"))
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")
