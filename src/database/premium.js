import db from "./db.js";
import { OWNER_ID, PREMIUM_VOTE_DURATION_MS } from "../config.js";

export function grantServerPremium(guildId, grantedBy) {
  if (grantedBy !== OWNER_ID) {
    throw new Error("Only the bot owner can grant permanent server premium.");
  }

  const stmt = db.prepare(`
    INSERT INTO premium_servers (guild_id, granted_by, granted_at)
    VALUES (?, ?, ?)
    ON CONFLICT(guild_id) DO UPDATE SET granted_by = excluded.granted_by, granted_at = excluded.granted_at
  `);

  stmt.run(guildId, grantedBy, Date.now());
}

export function isGuildPremium(guildId) {
  const row = db
    .prepare("SELECT guild_id FROM premium_servers WHERE guild_id = ?")
    .get(guildId);
  return !!row;
}

export function recordUserVote(userId) {
  const stmt = db.prepare(`
    INSERT INTO premium_votes (user_id, last_vote_at)
    VALUES (?, ?)
    ON CONFLICT(user_id) DO UPDATE SET last_vote_at = excluded.last_vote_at
  `);
  stmt.run(userId, Date.now());
}

export function hasActiveVotePremium(userId) {
  const row = db
    .prepare("SELECT last_vote_at FROM premium_votes WHERE user_id = ?")
    .get(userId);
  if (!row) return false;
  return Date.now() - row.last_vote_at < PREMIUM_VOTE_DURATION_MS;
}

export function isUserPremiumInGuild(userId, guildId) {
  if (isGuildPremium(guildId)) return true;
  return hasActiveVotePremium(userId);
}
