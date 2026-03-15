const { useQueue, QueueRepeatMode } = require('discord-player');
const { ctx }  = require('../../utils/ctx');
const E        = require('../../utils/embeds');
const { inVC, sameVC } = require('../../utils/permissions');

// ─── shared guard ─────────────────────────────────────────────────────────────
function guard(c, client, needsQueue = true) {
  if (!inVC(c.member)) return 'You must be in a voice channel!';
  if (!sameVC(c.member, client.player)) return 'You must be in the **same** voice channel as the bot!';
  if (needsQueue && !useQueue(c.guildId)) return 'Nothing is currently playing!';
  return null;
}

function make(name, aliases, fn) {
  return { name, aliases, execute: async (msg, args, client, isSlash = false) => {
    const c   = ctx(msg, isSlash);
    const err = guard(c, client);
    if (err) return c.reply({ embeds: [E.err(err)] });
    return fn(c, args, client, useQueue(c.guildId));
  }};
}

// ── PAUSE ─────────────────────────────────────────────────────────────────────
const pause = make('pause', [], (c, _, __, q) => {
  if (q.node.isPaused()) return c.reply({ embeds: [E.err('Already paused.')] });
  q.node.pause();
  return c.reply({ embeds: [E.ok('⏸ Paused.')] });
});

// ── RESUME ────────────────────────────────────────────────────────────────────
const resume = make('resume', [], (c, _, __, q) => {
  if (!q.node.isPaused()) return c.reply({ embeds: [E.err('Not paused.')] });
  q.node.resume();
  return c.reply({ embeds: [E.ok('▶️ Resumed.')] });
});

// ── SKIP ──────────────────────────────────────────────────────────────────────
const skip = make('skip', ['s'], (c, _, __, q) => {
  const t = q.currentTrack;
  q.node.skip();
  return c.reply({ embeds: [E.ok(`⏭ Skipped **${t?.title ?? 'track'}**.`)] });
});

// ── BACK ──────────────────────────────────────────────────────────────────────
const back = { name: 'back', aliases: ['b', 'prev', 'previous'],
  async execute(msg, args, client, isSlash = false) {
    const c = ctx(msg, isSlash);
    const err = guard(c, client);
    if (err) return c.reply({ embeds: [E.err(err)] });
    const q = useQueue(c.guildId);
    try {
      await q.history.back();
      return c.reply({ embeds: [E.ok('⏮ Playing previous track.')] });
    } catch {
      return c.reply({ embeds: [E.err('No previous track in history!')] });
    }
  },
};

// ── STOP ──────────────────────────────────────────────────────────────────────
const stop = make('stop', [], (c, _, __, q) => {
  q.delete();
  return c.reply({ embeds: [E.ok('⏹ Stopped and cleared the queue.')] });
});

// ── VOLUME ────────────────────────────────────────────────────────────────────
const volume = {
  name: 'volume', aliases: ['v', 'vol'],
  async execute(msg, args, client, isSlash = false) {
    const c = ctx(msg, isSlash);
    const err = guard(c, client);
    if (err) return c.reply({ embeds: [E.err(err)] });
    const q   = useQueue(c.guildId);
    const vol = isSlash ? msg.options.getInteger('level', true) : parseInt(args[0]);
    if (isNaN(vol) || vol < 1 || vol > 200)
      return c.reply({ embeds: [E.err('Volume must be between **1** and **200**.')] });
    q.node.setVolume(vol);
    const icon = vol === 0 ? '🔇' : vol < 50 ? '🔈' : vol < 150 ? '🔉' : '🔊';
    return c.reply({ embeds: [E.ok(`${icon} Volume set to **${vol}%**.`)] });
  },
};

// ── SEEK ──────────────────────────────────────────────────────────────────────
const seek = {
  name: 'seek',
  async execute(msg, args, client, isSlash = false) {
    const c = ctx(msg, isSlash);
    const err = guard(c, client);
    if (err) return c.reply({ embeds: [E.err(err)] });
    const q   = useQueue(c.guildId);
    const raw = isSlash ? msg.options.getString('time', true) : args[0];
    if (!raw) return c.reply({ embeds: [E.err('Provide a timestamp e.g. `1:30`')] });
    const parts = raw.split(':').reverse();
    const ms    = (+(parts[0] ?? 0) + +(parts[1] ?? 0) * 60 + +(parts[2] ?? 0) * 3600) * 1000;
    if (isNaN(ms)) return c.reply({ embeds: [E.err('Invalid time format. Use `mm:ss` or `hh:mm:ss`.')] });
    await q.node.seek(ms);
    return c.reply({ embeds: [E.ok(`⏩ Seeked to **${raw}**.`)] });
  },
};

// ── FORWARD ───────────────────────────────────────────────────────────────────
const forward = {
  name: 'forward', aliases: ['ff', 'fwd'],
  async execute(msg, args, client, isSlash = false) {
    const c = ctx(msg, isSlash);
    const err = guard(c, client);
    if (err) return c.reply({ embeds: [E.err(err)] });
    const q    = useQueue(c.guildId);
    const secs = isSlash ? (msg.options.getInteger('seconds') ?? 10) : (parseInt(args[0]) || 10);
    const ts   = q.node.getTimestamp();
    if (!ts) return c.reply({ embeds: [E.err('Cannot seek this track.')] });
    await q.node.seek(Math.min(ts.current.value + secs * 1000, ts.total.value - 1000));
    return c.reply({ embeds: [E.ok(`⏩ Forwarded **${secs}s**.`)] });
  },
};

// ── REWIND ────────────────────────────────────────────────────────────────────
const rewind = {
  name: 'rewind', aliases: ['rw', 'rew'],
  async execute(msg, args, client, isSlash = false) {
    const c = ctx(msg, isSlash);
    const err = guard(c, client);
    if (err) return c.reply({ embeds: [E.err(err)] });
    const q    = useQueue(c.guildId);
    const secs = isSlash ? (msg.options.getInteger('seconds') ?? 10) : (parseInt(args[0]) || 10);
    const ts   = q.node.getTimestamp();
    if (!ts) return c.reply({ embeds: [E.err('Cannot seek this track.')] });
    await q.node.seek(Math.max(ts.current.value - secs * 1000, 0));
    return c.reply({ embeds: [E.ok(`⏪ Rewound **${secs}s**.`)] });
  },
};

// ── NOW PLAYING ───────────────────────────────────────────────────────────────
const nowplaying = {
  name: 'nowplaying', aliases: ['np', 'now'],
  async execute(msg, args, client, isSlash = false) {
    const c = ctx(msg, isSlash);
    const q = useQueue(c.guildId);
    if (!q?.currentTrack) return c.reply({ embeds: [E.err('Nothing is playing.')] });
    return c.reply({ embeds: [E.nowPlaying(q.currentTrack, q)] });
  },
};

// ── SHUFFLE ───────────────────────────────────────────────────────────────────
const shuffle = make('shuffle', [], (c, _, __, q) => {
  if (q.tracks.size < 2) return c.reply({ embeds: [E.err('Need at least 2 songs to shuffle.')] });
  q.tracks.shuffle();
  return c.reply({ embeds: [E.ok(`🔀 Shuffled **${q.tracks.size}** songs.`)] });
});

// ── LOOP ──────────────────────────────────────────────────────────────────────
const loop = make('loop', [], (c, _, __, q) => {
  const modes  = [QueueRepeatMode.OFF, QueueRepeatMode.TRACK, QueueRepeatMode.QUEUE];
  const labels = ['🔁 Loop **off**.', '🔂 Looping **current track**.', '🔁 Looping **entire queue**.'];
  const next   = (q.repeatMode + 1) % modes.length;
  q.setRepeatMode(modes[next]);
  return c.reply({ embeds: [E.ok(labels[next])] });
});

// ── AUTOPLAY ──────────────────────────────────────────────────────────────────
const autoplay = make('autoplay', ['ap'], (c, _, __, q) => {
  const on = q.repeatMode === QueueRepeatMode.AUTOPLAY;
  q.setRepeatMode(on ? QueueRepeatMode.OFF : QueueRepeatMode.AUTOPLAY);
  q.metadata.autoplay = !on;
  return c.reply({ embeds: [E.ok(on ? '🎵 Autoplay **disabled**.' : '🎵 Autoplay **enabled** — I\'ll keep the music going!')] });
});

// ── SKIPTO ────────────────────────────────────────────────────────────────────
const skipto = {
  name: 'skipto', aliases: ['st', 'jump'],
  async execute(msg, args, client, isSlash = false) {
    const c = ctx(msg, isSlash);
    const err = guard(c, client);
    if (err) return c.reply({ embeds: [E.err(err)] });
    const q   = useQueue(c.guildId);
    const pos = isSlash ? msg.options.getInteger('position', true) : parseInt(args[0]);
    if (isNaN(pos) || pos < 1 || pos > q.tracks.size)
      return c.reply({ embeds: [E.err(`Invalid position. Queue has **${q.tracks.size}** songs.`)] });
    q.node.skipTo(pos - 1);
    return c.reply({ embeds: [E.ok(`⏭ Skipped to position **${pos}**.`)] });
  },
};

// ── REMOVE ────────────────────────────────────────────────────────────────────
const remove = {
  name: 'remove', aliases: ['rm'],
  async execute(msg, args, client, isSlash = false) {
    const c = ctx(msg, isSlash);
    const err = guard(c, client);
    if (err) return c.reply({ embeds: [E.err(err)] });
    const q   = useQueue(c.guildId);
    const pos = isSlash ? msg.options.getInteger('position', true) : parseInt(args[0]);
    if (isNaN(pos) || pos < 1 || pos > q.tracks.size)
      return c.reply({ embeds: [E.err(`Invalid position.`)] });
    const t = q.tracks.at(pos - 1);
    q.removeTrack(pos - 1);
    return c.reply({ embeds: [E.ok(`🗑 Removed **${t.title}**.`)] });
  },
};

// ── MOVE ──────────────────────────────────────────────────────────────────────
const move = {
  name: 'move',
  async execute(msg, args, client, isSlash = false) {
    const c    = ctx(msg, isSlash);
    const err  = guard(c, client);
    if (err) return c.reply({ embeds: [E.err(err)] });
    const q    = useQueue(c.guildId);
    const from = isSlash ? msg.options.getInteger('from', true) : parseInt(args[0]);
    const to   = isSlash ? msg.options.getInteger('to', true)   : parseInt(args[1]);
    if ([from, to].some(n => isNaN(n) || n < 1 || n > q.tracks.size))
      return c.reply({ embeds: [E.err(`Invalid positions. Queue has **${q.tracks.size}** songs.`)] });
    const arr = q.tracks.toArray();
    const [t] = arr.splice(from - 1, 1);
    arr.splice(to - 1, 0, t);
    q.tracks.clear();
    arr.forEach(x => q.addTrack(x));
    return c.reply({ embeds: [E.ok(`↕️ Moved **${t.title}** to position **${to}**.`)] });
  },
};

// ── CLEAR ─────────────────────────────────────────────────────────────────────
const clear = make('clear', [], (c, _, __, q) => {
  const n = q.tracks.size;
  q.tracks.clear();
  return c.reply({ embeds: [E.ok(`🧹 Cleared **${n}** songs from the queue.`)] });
});

// ── LEAVE ─────────────────────────────────────────────────────────────────────
const leave = {
  name: 'leave', aliases: ['dc', 'disconnect'],
  async execute(msg, args, client, isSlash = false) {
    const c = ctx(msg, isSlash);
    const q = useQueue(c.guildId);
    if (!q) return c.reply({ embeds: [E.err('Not in a voice channel.')] });
    q.delete();
    return c.reply({ embeds: [E.ok('👋 Disconnected.')] });
  },
};

module.exports = {
  pause, resume, skip, back, stop,
  volume, seek, forward, rewind,
  nowplaying, shuffle, loop, autoplay,
  skipto, remove, move, clear, leave,
};
