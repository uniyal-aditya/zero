// ── Node 18 polyfills (undici / discord.js need File & Blob globals) ──────────
const { Blob } = require('buffer');
if (typeof globalThis.Blob === 'undefined') globalThis.Blob = Blob;
if (typeof globalThis.File === 'undefined') {
  class File extends Blob {
    constructor(chunks, name, opts = {}) {
      super(chunks, opts);
      this.name = name;
      this.lastModified = opts.lastModified ?? Date.now();
    }
  }
  globalThis.File = File;
}

require('dotenv').config();
const { Client, GatewayIntentBits, Collection } = require('discord.js');
const { Player }             = require('discord-player');
const { SpotifyExtractor }   = require('@discord-player/extractor');
const { YoutubeiExtractor }  = require('discord-player-youtubei');
const fs   = require('fs');
const path = require('path');
const cfg  = require('./config');
const E    = require('./utils/embeds');

// ── CLIENT SETUP ──────────────────────────────────────────────────────────────
const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
    GatewayIntentBits.GuildVoiceStates,
    GatewayIntentBits.GuildMembers,
  ],
});

// ── PLAYER ────────────────────────────────────────────────────────────────────
const player = new Player(client, {
  ytdlOptions: {
    quality: 'highestaudio',
    highWaterMark: 1 << 25,
    filter: 'audioonly',
  },
});
client.player = player;

(async () => {
  await player.extractors.register(YoutubeiExtractor, {});
  await player.extractors.register(SpotifyExtractor, {
    clientId: cfg.spotifyClientId,
    clientSecret: cfg.spotifyClientSecret,
  });
  await player.extractors.loadDefault((ext) => ext !== 'YouTubeExtractor');
})();

// ── COMMAND STORE ─────────────────────────────────────────────────────────────
client.commands = new Collection();   // prefix
client.slash    = new Collection();   // slash

function loadCommands(dir) {
  for (const file of fs.readdirSync(dir)) {
    const full = path.join(dir, file);
    if (fs.statSync(full).isDirectory()) { loadCommands(full); continue; }
    if (!file.endsWith('.js')) continue;
    const exports = require(full);
    // Support both single-export and multi-export files
    const cmds = Array.isArray(exports) ? exports : Object.values(exports);
    for (const cmd of cmds) {
      if (!cmd?.name) continue;
      client.commands.set(cmd.name, cmd);
      if (cmd.aliases) cmd.aliases.forEach(a => client.commands.set(a, cmd));
    }
  }
}
loadCommands(path.join(__dirname, 'commands'));

// ── LOAD EVENTS ───────────────────────────────────────────────────────────────
for (const file of fs.readdirSync(path.join(__dirname, 'events')).filter(f => f.endsWith('.js'))) {
  const ev = require(path.join(__dirname, 'events', file));
  client[ev.once ? 'once' : 'on'](ev.name, (...a) => ev.execute(...a, client, player));
}

// ── PLAYER EVENTS ─────────────────────────────────────────────────────────────
player.events.on('playerStart', (queue, track) => {
  queue.metadata?.channel?.send({ embeds: [E.nowPlaying(track, queue)] }).catch(() => {});
});

player.events.on('audioTrackAdd', (queue, track) => {
  // Only show if queue already had a track (suppress initial play embed double)
  if (queue.node.isPlaying()) {
    queue.metadata?.channel?.send({ embeds: [E.addedToQueue(track, queue)] }).catch(() => {});
  }
});

player.events.on('disconnect', queue => {
  queue.metadata?.channel?.send({ embeds: [E.err('Disconnected from voice channel.')] }).catch(() => {});
});

player.events.on('emptyQueue', queue => {
  if (queue.metadata?.autoplay) return;
  queue.metadata?.channel?.send({ embeds: [E.info('Queue Ended', 'No more tracks. Use `-autoplay` or queue more songs!')] }).catch(() => {});
});

player.events.on('error', (queue, error) => {
  console.error('[Player Error]', error);
  queue.metadata?.channel?.send({ embeds: [E.err(`Player error: ${error.message}`)] }).catch(() => {});
});

client.login(cfg.token);
