const { useMainPlayer, useQueue } = require('discord-player');
const { EmbedBuilder } = require('discord.js');
const { ctx }  = require('../../utils/ctx');
const E        = require('../../utils/embeds');
const db       = require('../../utils/database');
const { inVC } = require('../../utils/permissions');

// ── LIKE ──────────────────────────────────────────────────────────────────────
const like = {
  name: 'like',
  description: 'Like the currently playing song',
  async execute(msg, args, client, isSlash = false) {
    const c = ctx(msg, isSlash);
    const q = useQueue(c.guildId);
    if (!q?.currentTrack) return c.reply({ embeds: [E.err('Nothing is playing!')] });
    const t = q.currentTrack;
    if (!db.likeSong(c.user.id, { title: t.title, url: t.url, duration: t.duration, thumbnail: t.thumbnail, author: t.author }))
      return c.reply({ embeds: [E.err('This song is already in your liked songs!')] });
    return c.reply({ embeds: [E.ok(`❤️ Added **${t.title}** to your liked songs.`)] });
  },
};

// ── UNLIKE ────────────────────────────────────────────────────────────────────
const unlike = {
  name: 'unlike',
  description: 'Unlike the currently playing song',
  async execute(msg, args, client, isSlash = false) {
    const c = ctx(msg, isSlash);
    const q = useQueue(c.guildId);
    if (!q?.currentTrack) return c.reply({ embeds: [E.err('Nothing is playing!')] });
    const t = q.currentTrack;
    if (!db.unlikeSong(c.user.id, t.url))
      return c.reply({ embeds: [E.err('This song is not in your liked songs.')] });
    return c.reply({ embeds: [E.ok(`💔 Removed **${t.title}** from liked songs.`)] });
  },
};

// ── LIKED ─────────────────────────────────────────────────────────────────────
const liked = {
  name: 'liked',
  aliases: ['favorites', 'fav'],
  description: 'View or play your liked songs',
  async execute(msg, args, client, isSlash = false) {
    const c   = ctx(msg, isSlash);
    const uid = c.user.id;
    const sub = args[0]?.toLowerCase();

    // Play all liked songs
    if (sub === 'play' || sub === 'start') {
      if (!inVC(c.member)) return c.reply({ embeds: [E.err('You must be in a voice channel!')] });
      const songs = db.getLikedSongs(uid);
      if (!songs.length) return c.reply({ embeds: [E.err('Your liked songs list is empty!')] });
      await c.reply({ embeds: [E.ok(`▶️ Loading **${songs.length}** liked songs…`)] });
      const player = useMainPlayer();
      let loaded = 0;
      for (const song of songs) {
        try {
          await player.play(c.member.voice.channel, song.url, {
            nodeOptions: { metadata: { channel: c.channel, requestedBy: c.user }, volume: db.getSettings(c.guildId).defaultVolume ?? 80 },
            requestedBy: c.user,
          });
          loaded++;
        } catch {}
      }
      return c.channel.send({ embeds: [E.ok(`✅ Queued **${loaded}** liked songs.`)] });
    }

    // View liked songs
    const songs = db.getLikedSongs(uid);
    return c.reply({
      embeds: [new EmbedBuilder()
        .setColor(0xED4245)
        .setTitle(`❤️  ${c.user.username}'s Liked Songs`)
        .setDescription(
          songs.length
            ? songs.slice(0, 20).map((s, i) => `\`${i + 1}.\` [${s.title}](${s.url}) — \`${s.duration}\``).join('\n')
            : 'No liked songs yet!\nUse `-like` while a song is playing to add it here.'
        )
        .setFooter({ text: `${songs.length} songs • -liked play to queue all • Made by Aditya</>` })],
    });
  },
};

module.exports = { like, unlike, liked };
