from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class ZeroConfig:
    discord_token: str = os.getenv("DISCORD_TOKEN", "")
    discord_client_id: str = os.getenv("DISCORD_CLIENT_ID", "")
    owner_id: int = int(os.getenv("OWNER_ID", "800553680704110624"))
    prefix: str = os.getenv("PREFIX", "-")

    topgg_token: str = os.getenv("TOPGG_TOKEN", "")
    topgg_webhook_auth: str = os.getenv("TOPGG_WEBHOOK_AUTH", "")
    topgg_webhook_port: int = int(os.getenv("TOPGG_WEBHOOK_PORT", "3001"))

    premium_vote_duration_sec: int = 12 * 60 * 60


CONFIG = ZeroConfig()

