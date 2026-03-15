require('dotenv').config();

module.exports = {
  // ─── BOT ────────────────────────────────────────────────────────────────────
  token: process.env.DISCORD_TOKEN,
  prefix: '-',
  ownerId: '800553680704110624',         // Aditya's Discord ID

  // ─── SPOTIFY ────────────────────────────────────────────────────────────────
  spotifyClientId: process.env.SPOTIFY_CLIENT_ID,
  spotifyClientSecret: process.env.SPOTIFY_CLIENT_SECRET,

  // ─── TOP.GG ─────────────────────────────────────────────────────────────────
  topggToken: process.env.TOPGG_TOKEN,
  topggBotId: process.env.TOPGG_BOT_ID,
  voteRewardHours: 12,

  // ─── BOT INFO ────────────────────────────────────────────────────────────────
  botName: 'Zero',
  version: '1.0.0',
  supportServer: 'https://discord.gg/yourinvite',   // replace with your server

  // ─── COLORS ─────────────────────────────────────────────────────────────────
  colors: {
    primary:  0x5865F2,
    success:  0x57F287,
    error:    0xED4245,
    warning:  0xFEE75C,
    premium:  0xFFD700,
    info:     0x5865F2,
    dark:     0x2B2D31,
  },

  // ─── PREMIUM FEATURE LIST ────────────────────────────────────────────────────
  premiumFeatures: [
    '🎛️ Audio Filters (Bass, 8D, Nightcore, Vaporwave…)',
    '🔒 24/7 Mode — bot stays in VC forever',
    '🎧 Custom DJ Role configuration',
    '⚡ Priority Queue (skip to front)',
    '📻 Unlimited queue size',
    '🎵 Autoplay from related tracks',
    '🔊 HD Audio Quality (highest bitrate)',
    '📁 Unlimited server playlists',
    '💾 Default volume per server',
  ],
};
