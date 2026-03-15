const { useMainPlayer, useQueue } = require('discord-player');
const { EmbedBuilder } = require('discord.js');
const { ctx }  = require('../../utils/ctx');
const E        = require('../../utils/embeds');
const db       = require('../../utils/database');
const { inVC } = require('../../utils/permissions');

module.exports = {
  name: 'pl',
  aliases: ['playlist'],
  description: 'Manage personal playlists',

  async execute(msg, args, client, isSlash = false) {
    const c   = ctx(msg, isSlash);
    const uid = c.user.id;
    const sub = args[0]?.toLowerCase();

    if (!sub)
      return c.reply({ embeds: [E.err('Usage: `-pl <create|delete|list|view|add|remove|play|rename>`')] });

    switch (sub) {

      // ── CREATE ──────────────────────────────────────────────────────────────
      case 'create': {
        const name = args.slice(1).join(' ').trim();
        if (!name) return c.reply({ embeds: [E.err('Provide a playlist name.')] });
        if (name.length > 32) return c.reply({ embeds: [E.err('Name must be ≤ 32 characters.')] });
        const playlists = db.getPlaylists(uid);
        if (Object.keys(playlists).length >= 25)
          return c.reply({ embeds: [E.err('You can have at most **25** playlists.')] });
        if (!db.createPlaylist(uid, name))
          return c.reply({ embeds: [E.err(`A playlist named **${name}** already exists.`)] });
        return c.reply({ embeds: [E.ok(`📁 Created playlist **${name}**.`)] });
      }

      // ── DELETE ──────────────────────────────────────────────────────────────
      case 'delete':
      case 'del': {
        const name = args.slice(1).join(' ').trim();
        if (!name) return c.reply({ embeds: [E.err('Provide the playlist name.')] });
        if (!db.deletePlaylist(uid, name))
          return c.reply({ embeds: [E.err(`No playlist named **${name}** found.`)] });
        return c.reply({ embeds: [E.ok(`🗑 Deleted **${name}**.`)] });
      }

      // ── LIST ────────────────────────────────────────────────────────────────
      case 'list': {
        const all = Object.values(db.getPlaylists(uid));
        if (!all.length)
          return c.reply({ embeds: [E.err('You have no playlists. Create one with `-pl create <n>`.')] });
        return c.reply({
          embeds: [new EmbedBuilder()
            .setColor(0x5865F2)
            .setTitle(`📁  ${c.user.username}'s Playlists`)
            .setDescription(all.map((p, i) => `**${i + 1}.** ${p.name} — ${p.songs.length} songs`).join('\n'))
            .setFooter({ text: `${all.length}/25 playlists • Made by Aditya</>` })],
        });
      }

      // ── VIEW ────────────────────────────────────────────────────────────────
      case 'view':
      case 'show': {
        const name = args.slice(1).join(' ').trim();
        if (!name) return c.reply({ embeds: [E.err('Provide the playlist name.')] });
        const pl = db.getPlaylist(uid, name);
        if (!pl) return c.reply({ embeds: [E.err(`No playlist named **${name}** found.`)] });
        return c.reply({
          embeds: [new EmbedBuilder()
            .setColor(0x5865F2)
            .setTitle(`📁  ${pl.name}`)
            .setDescription(
              pl.songs.length
                ? pl.songs.slice(0, 20).map((s, i) => `\`${i + 1}.\` [${s.title}](${s.url}) — \`${s.duration}\``).join('\n')
                : 'No songs yet. Use `-pl add <n>` while a song plays.'
            )
            .setFooter({ text: `${pl.songs.length} songs${pl.songs.length > 20 ? ' (showing first 20)' : ''} • Made by Aditya</>` })],
        });
      }

      // ── ADD ─────────────────────────────────────────────────────────────────
      case 'add':
      case 'save': {
        const name = args.slice(1).join(' ').trim();
        if (!name) return c.reply({ embeds: [E.err('Provide the playlist name.')] });
        const q = useQueue(c.guildId);
        if (!q?.currentTrack) return c.reply({ embeds: [E.err('Nothing is playing right now.')] });
        const t = q.currentTrack;
        if (!db.addSongToPlaylist(uid, name, { title: t.title, url: t.url, duration: t.duration, thumbnail: t.thumbnail, author: t.author }))
          return c.reply({ embeds: [E.err(`No playlist named **${name}** found.`)] });
        return c.reply({ embeds: [E.ok(`✅ Added **${t.title}** to **${name}**.`)] });
      }

      // ── REMOVE ──────────────────────────────────────────────────────────────
      case 'remove':
      case 'rm': {
        const name = args[1]; const pos = parseInt(args[2]);
        if (!name || isNaN(pos)) return c.reply({ embeds: [E.err('Usage: `-pl remove <playlist> <position>`')] });
        if (!db.removeSongFromPlaylist(uid, name, pos - 1))
          return c.reply({ embeds: [E.err('Invalid playlist name or position.')] });
        return c.reply({ embeds: [E.ok(`🗑 Removed song #${pos} from **${name}**.`)] });
      }

      // ── PLAY ────────────────────────────────────────────────────────────────
      case 'play':
      case 'start': {
        const name = args.slice(1).join(' ').trim();
        if (!name) return c.reply({ embeds: [E.err('Provide the playlist name.')] });
        if (!inVC(c.member)) return c.reply({ embeds: [E.err('You must be in a voice channel!')] });
        const pl = db.getPlaylist(uid, name);
        if (!pl) return c.reply({ embeds: [E.err(`No playlist named **${name}** found.`)] });
        if (!pl.songs.length) return c.reply({ embeds: [E.err(`**${name}** is empty.`)] });
        await c.reply({ embeds: [E.ok(`▶️ Loading **${pl.name}** (${pl.songs.length} songs)…`)] });
        const player = useMainPlayer();
        let loaded = 0;
        for (const song of pl.songs) {
          try {
            await player.play(c.member.voice.channel, song.url, {
              nodeOptions: { metadata: { channel: c.channel, requestedBy: c.user }, volume: db.getSettings(c.guildId).defaultVolume ?? 80 },
              requestedBy: c.user,
            });
            loaded++;
          } catch {}
        }
        return c.channel.send({ embeds: [E.ok(`✅ Loaded **${loaded}/${pl.songs.length}** songs from **${pl.name}**.`)] });
      }

      // ── RENAME ──────────────────────────────────────────────────────────────
      case 'rename': {
        const oldN = args[1]; const newN = args.slice(2).join(' ').trim();
        if (!oldN || !newN) return c.reply({ embeds: [E.err('Usage: `-pl rename <old> <new>`')] });
        const res = db.renamePlaylist(uid, oldN, newN);
        if (res === false) return c.reply({ embeds: [E.err(`No playlist named **${oldN}** found.`)] });
        if (res === 'exists') return c.reply({ embeds: [E.err(`**${newN}** already exists.`)] });
        return c.reply({ embeds: [E.ok(`✏️ Renamed **${oldN}** → **${newN}**.`)] });
      }

      default:
        return c.reply({ embeds: [E.err('Unknown subcommand. Valid: `create` `delete` `list` `view` `add` `remove` `play` `rename`')] });
    }
  },
};
