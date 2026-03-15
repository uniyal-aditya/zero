const fs   = require('fs');
const path = require('path');

const DIR = path.join(__dirname, '..', '..', 'data');

class Database {
  constructor() {
    if (!fs.existsSync(DIR)) fs.mkdirSync(DIR, { recursive: true });
    ['premium', 'votes', 'playlists', 'likedSongs', 'settings'].forEach(f => {
      const p = this._fp(f);
      if (!fs.existsSync(p)) fs.writeFileSync(p, '{}');
    });
  }

  _fp(name) { return path.join(DIR, `${name}.json`); }
  _r(name)  { try { return JSON.parse(fs.readFileSync(this._fp(name), 'utf8')); } catch { return {}; } }
  _w(name, d) { fs.writeFileSync(this._fp(name), JSON.stringify(d, null, 2)); }

  // ── PREMIUM (server-level, owner only) ──────────────────────────────────────
  isPremiumGuild(guildId) { return this._r('premium')[guildId]?.active === true; }

  grantPremium(guildId, by) {
    const d = this._r('premium');
    d[guildId] = { active: true, grantedBy: by, grantedAt: Date.now() };
    this._w('premium', d);
  }

  revokePremium(guildId) {
    const d = this._r('premium');
    if (d[guildId]) { d[guildId].active = false; d[guildId].revokedAt = Date.now(); }
    this._w('premium', d);
  }

  getAllPremiumGuilds() {
    return Object.entries(this._r('premium')).filter(([,v]) => v.active).map(([k]) => k);
  }

  getPremiumInfo(guildId) { return this._r('premium')[guildId] || null; }

  // ── VOTE PREMIUM (user-level, 12hr) ──────────────────────────────────────────
  grantVotePremium(userId) {
    const d = this._r('votes');
    d[userId] = { expiresAt: Date.now() + 12 * 3600 * 1000, votedAt: Date.now() };
    this._w('votes', d);
  }

  hasVotePremium(userId) {
    const d = this._r('votes')[userId];
    return !!d && d.expiresAt > Date.now();
  }

  getVoteExpiry(userId) { return this._r('votes')[userId]?.expiresAt || null; }

  // ── ACCESS CHECK ────────────────────────────────────────────────────────────
  hasAccess(guildId, userId) {
    return this.isPremiumGuild(guildId) || this.hasVotePremium(userId);
  }

  // ── PLAYLISTS ────────────────────────────────────────────────────────────────
  getPlaylists(userId) { return this._r('playlists')[userId] || {}; }

  getPlaylist(userId, name) { return this.getPlaylists(userId)[name.toLowerCase()] || null; }

  createPlaylist(userId, name) {
    const d = this._r('playlists');
    if (!d[userId]) d[userId] = {};
    const k = name.toLowerCase();
    if (d[userId][k]) return false;
    d[userId][k] = { name, songs: [], createdAt: Date.now() };
    this._w('playlists', d); return true;
  }

  deletePlaylist(userId, name) {
    const d = this._r('playlists');
    const k = name.toLowerCase();
    if (!d[userId]?.[k]) return false;
    delete d[userId][k]; this._w('playlists', d); return true;
  }

  addSongToPlaylist(userId, name, song) {
    const d = this._r('playlists');
    const k = name.toLowerCase();
    if (!d[userId]?.[k]) return false;
    d[userId][k].songs.push({ ...song, addedAt: Date.now() });
    this._w('playlists', d); return true;
  }

  removeSongFromPlaylist(userId, name, idx) {
    const d = this._r('playlists');
    const k = name.toLowerCase();
    const songs = d[userId]?.[k]?.songs;
    if (!songs || idx < 0 || idx >= songs.length) return false;
    songs.splice(idx, 1); this._w('playlists', d); return true;
  }

  renamePlaylist(userId, oldName, newName) {
    const d = this._r('playlists');
    const ok = oldName.toLowerCase(), nk = newName.toLowerCase();
    if (!d[userId]?.[ok]) return false;
    if (d[userId][nk]) return 'exists';
    d[userId][nk] = { ...d[userId][ok], name: newName };
    delete d[userId][ok]; this._w('playlists', d); return true;
  }

  // ── LIKED SONGS ───────────────────────────────────────────────────────────────
  getLikedSongs(userId) { return this._r('likedSongs')[userId] || []; }

  likeSong(userId, song) {
    const d = this._r('likedSongs');
    if (!d[userId]) d[userId] = [];
    if (d[userId].find(s => s.url === song.url)) return false;
    d[userId].unshift({ ...song, likedAt: Date.now() });
    this._w('likedSongs', d); return true;
  }

  unlikeSong(userId, url) {
    const d = this._r('likedSongs');
    if (!d[userId]) return false;
    const prev = d[userId].length;
    d[userId] = d[userId].filter(s => s.url !== url);
    if (d[userId].length === prev) return false;
    this._w('likedSongs', d); return true;
  }

  isLiked(userId, url) { return this.getLikedSongs(userId).some(s => s.url === url); }

  // ── SETTINGS ─────────────────────────────────────────────────────────────────
  getSettings(guildId) {
    return this._r('settings')[guildId] || { djRole: null, tfSeven: false, defaultVolume: 80 };
  }

  setSetting(guildId, key, value) {
    const d = this._r('settings');
    if (!d[guildId]) d[guildId] = {};
    d[guildId][key] = value; this._w('settings', d);
  }
}

module.exports = new Database();
