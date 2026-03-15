import os
from dotenv import load_dotenv

load_dotenv()

# ── BOT ───────────────────────────────────────────────────────────────────────
TOKEN        = os.getenv("DISCORD_TOKEN")
OWNER_ID     = int(os.getenv("OWNER_ID", "800553680704110624"))
PREFIX       = "-"
BOT_VERSION  = "1.0.0"
CLIENT_ID    = "1462040223872581797"
SUPPORT_URL  = "https://discord.gg/mb7nsqUx6U"
INVITE_URL   = "https://discord.com/oauth2/authorize?client_id=1462040223872581797&permissions=8845475720850496&response_type=code&redirect_uri=https%3A%2F%2Fdiscord.gg%2FUAd3waUyD3&integration_type=0&scope=voice+applications.commands+bot"

# ── LAVALINK ──────────────────────────────────────────────────────────────────
LAVALINK_HOST     = os.getenv("LAVALINK_HOST", "localhost")
LAVALINK_PORT     = int(os.getenv("LAVALINK_PORT", "2333"))
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")

# ── SPOTIFY ───────────────────────────────────────────────────────────────────
SPOTIFY_CLIENT_ID     = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")

# ── TOP.GG ────────────────────────────────────────────────────────────────────
TOPGG_TOKEN  = os.getenv("TOPGG_TOKEN", "")
TOPGG_BOT_ID = os.getenv("TOPGG_BOT_ID", "")
VOTE_URL     = f"https://top.gg/bot/{TOPGG_BOT_ID}/vote"
VOTE_HOURS   = 12

# ── COLOURS ───────────────────────────────────────────────────────────────────
COL_PRIMARY = 0x5865F2
COL_SUCCESS = 0x57F287
COL_ERROR   = 0xED4245
COL_WARNING = 0xFEE75C
COL_PREMIUM = 0xFFD700
COL_DARK    = 0x2B2D31

# ── PREMIUM FEATURES ─────────────────────────────────────────────────────────
PREMIUM_FEATURES = [
    "🎛️  Audio Filters — Bass Boost, 8D, Nightcore, Vaporwave…",
    "🔒  24/7 Mode — bot stays in VC permanently",
    "🎧  Custom DJ Role",
    "⚡  Priority Queue (jump to front)",
    "🔊  HD Audio (highest quality)",
    "🎵  Autoplay — related songs when queue ends",
    "📁  Unlimited server playlists",
    "💾  Custom default volume per server",
]
