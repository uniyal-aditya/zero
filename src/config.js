import dotenv from "dotenv";
dotenv.config();

export const OWNER_ID = process.env.OWNER_ID || "800553680704110624";
export const DEFAULT_PREFIX = process.env.DEFAULT_PREFIX || "-";

export const DISCORD_TOKEN = process.env.DISCORD_TOKEN || "";
export const DISCORD_CLIENT_ID = process.env.DISCORD_CLIENT_ID || "";
export const DISCORD_GUILD_ID = process.env.DISCORD_GUILD_ID || "";

export const TOPGG_TOKEN = process.env.TOPGG_TOKEN || "";
export const TOPGG_WEBHOOK_AUTH = process.env.TOPGG_WEBHOOK_AUTH || "";
export const TOPGG_WEBHOOK_PORT = Number(process.env.TOPGG_WEBHOOK_PORT || 3000);

export const PREMIUM_VOTE_DURATION_MS = 12 * 60 * 60 * 1000; // 12 hours
