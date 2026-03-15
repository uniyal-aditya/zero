const { EmbedBuilder, ActionRowBuilder, StringSelectMenuBuilder, ButtonBuilder, ButtonStyle } = require('discord.js');
const cfg = require('../config');
const C = cfg.colors;

const footer = { text: `Zero Music • Made by Aditya</>`, iconURL: null };

// ─── HELPERS ──────────────────────────────────────────────────────────────────
function progressBar(queue) {
  const ts = queue?.node?.getTimestamp?.();
  if (!ts) return '';
  const pct = Math.floor((ts.current.value / (ts.total.value || 1)) * 100);
  const fill = Math.round(pct / 5);
  return `\`${ts.current.label}\` ${'█'.repeat(fill)}${'░'.repeat(20 - fill)} \`${ts.total.label}\``;
}

function loopLabel(mode) {
  return ['Off', '🔂 Track', '🔁 Queue', '♾️ Autoplay'][mode] ?? 'Off';
}

// ─── NOW PLAYING ─────────────────────────────────────────────────────────────
function nowPlaying(track, queue) {
  return new EmbedBuilder()
    .setColor(C.primary)
    .setAuthor({ name: '♪  Now Playing' })
    .setTitle(track.title)
    .setURL(track.url)
    .setThumbnail(track.thumbnail)
    .addFields(
      { name: '👤 Artist',     value: track.author   || 'Unknown', inline: true },
      { name: '⏱ Duration',   value: track.duration || 'Live',    inline: true },
      { name: '📋 Requested', value: `${track.requestedBy}`,       inline: true },
      { name: '🔄 Loop',      value: loopLabel(queue.repeatMode),  inline: true },
      { name: '🔊 Volume',    value: `${queue.node.volume}%`,      inline: true },
      { name: '📃 In Queue',  value: `${queue.tracks.size} tracks`,inline: true },
      { name: '\u200B',       value: progressBar(queue) || '\u200B', inline: false },
    )
    .setFooter(footer);
}

// ─── ADDED TO QUEUE ───────────────────────────────────────────────────────────
function addedToQueue(track, queue) {
  return new EmbedBuilder()
    .setColor(C.success)
    .setAuthor({ name: '✅  Added to Queue' })
    .setTitle(track.title)
    .setURL(track.url)
    .setThumbnail(track.thumbnail)
    .addFields(
      { name: '👤 Artist',   value: track.author   || 'Unknown', inline: true },
      { name: '⏱ Duration', value: track.duration || 'Live',    inline: true },
      { name: '# Position', value: `#${queue.tracks.size}`,      inline: true },
    )
    .setFooter({ text: `Requested by ${track.requestedBy?.tag ?? 'Unknown'}` });
}

// ─── QUEUE ────────────────────────────────────────────────────────────────────
function queueEmbed(queue, page = 1) {
  const tracks  = queue.tracks.toArray();
  const perPage = 10;
  const pages   = Math.max(1, Math.ceil(tracks.length / perPage));
  page = Math.min(Math.max(page, 1), pages);
  const slice   = tracks.slice((page - 1) * perPage, page * perPage);
  const now     = queue.currentTrack;

  return new EmbedBuilder()
    .setColor(C.primary)
    .setTitle('📋  Music Queue')
    .setDescription(
      slice.map((t, i) =>
        `\`${(page - 1) * perPage + i + 1}.\` [${t.title}](${t.url}) — \`${t.duration}\` · ${t.requestedBy}`
      ).join('\n') || 'Queue is empty.'
    )
    .addFields({
      name: '♪ Now Playing',
      value: now ? `[${now.title}](${now.url}) — \`${now.duration}\`` : 'Nothing',
    })
    .setFooter({ text: `Page ${page}/${pages} • ${tracks.length} tracks total • Made by Aditya</>` });
}

// ─── ERROR / SUCCESS / INFO ───────────────────────────────────────────────────
const err  = msg => new EmbedBuilder().setColor(C.error).setDescription(`❌  ${msg}`);
const ok   = msg => new EmbedBuilder().setColor(C.success).setDescription(`✅  ${msg}`);
const info = (title, desc) => new EmbedBuilder().setColor(C.info).setTitle(title).setDescription(desc).setFooter(footer);

// ─── PREMIUM WALL ─────────────────────────────────────────────────────────────
function premiumWall() {
  return new EmbedBuilder()
    .setColor(C.premium)
    .setTitle('⭐  Zero Premium Required')
    .setDescription(
      '**This feature requires Zero Premium.**\n\n' +
      '> 🗳️ **Vote on Top.gg** for **12 hours** of free premium!\n' +
      `> [Click here to vote →](https://top.gg/bot/${cfg.topggBotId}/vote)\n\n` +
      '> 👑 **Server Premium** — contact the bot owner to grant your server.'
    )
    .setFooter(footer);
}

// ─── ABOUT EMBED (fires when bot is @mentioned) ───────────────────────────────
function aboutEmbed(client, mentionerTag) {
  return new EmbedBuilder()
    .setColor(C.primary)
    .setTitle(`🎵  Zero Music Bot`)
    .setDescription(
      `Hey ${mentionerTag ? `**${mentionerTag}**` : 'there'}! 👋\n\n` +
      `I'm **Zero**, a high-definition music bot packed with every feature you need.\n\n` +
      `**📌 Quick Start**\n` +
      `\`-play <song / URL>\` — Play any song\n` +
      `\`-help\` — Full interactive command menu\n\n` +
      `**🔗 Supports:** YouTube • Spotify (tracks, albums, playlists)\n` +
      `**🎛️ Prefix:** \`-\`  •  **Slash commands:** \`/play\`, \`/help\`…`
    )
    .addFields(
      { name: '📊 Stats',     value: `**${client.guilds.cache.size}** servers\n**${client.ws.ping}ms** ping`, inline: true },
      { name: '⭐ Premium',   value: `[Vote on Top.gg](https://top.gg/bot/${cfg.topggBotId}/vote) for 12hr free premium!`, inline: true },
      { name: '🛠 Version',   value: cfg.version, inline: true },
    )
    .setThumbnail(client.user.displayAvatarURL())
    .setFooter({ text: `Zero Music • Made by Aditya</>  •  Prefix: -` });
}

// ─── HELP MENU (main selector) ────────────────────────────────────────────────
function helpMain(client) {
  const embed = new EmbedBuilder()
    .setColor(C.primary)
    .setTitle('🎵  Zero Music — Help')
    .setDescription(
      '**Select a category below** to view its commands.\n\n' +
      '> 🎵 **Music** — Playback, seek, volume, lyrics\n' +
      '> 📋 **Queue** — View, manage, shuffle, loop\n' +
      '> 📁 **Playlists** — Create & manage personal playlists\n' +
      '> ❤️ **Liked Songs** — Your personal favorites\n' +
      '> ⭐ **Premium** — Filters, 24/7, DJ role & more\n' +
      '> 👑 **Owner** — Bot management (restricted)\n\n' +
      `**Prefix:** \`-\`  •  **Slash:** \`/\`  •  **Support:** ${cfg.supportServer}`
    )
    .setThumbnail(client.user.displayAvatarURL())
    .setFooter({ text: 'Zero Music • Made by Aditya</>' });

  const menu = new ActionRowBuilder().addComponents(
    new StringSelectMenuBuilder()
      .setCustomId('help_menu')
      .setPlaceholder('📂  Choose a category…')
      .addOptions([
        { label: '🎵 Music',        value: 'music',     description: 'Play, pause, skip, seek, volume, lyrics' },
        { label: '📋 Queue',        value: 'queue',     description: 'View queue, shuffle, loop, remove, move' },
        { label: '📁 Playlists',    value: 'playlist',  description: 'Create, delete, play personal playlists' },
        { label: '❤️ Liked Songs',  value: 'liked',     description: 'Like songs, view & play liked songs' },
        { label: '⭐ Premium',      value: 'premium',   description: 'Audio filters, 24/7 mode, DJ role & more' },
        { label: '👑 Owner',        value: 'owner',     description: 'Owner-only bot management commands' },
      ])
  );

  return { embed, menu };
}

// ─── HELP CATEGORY EMBEDS ────────────────────────────────────────────────────
function helpCategory(cat) {
  const data = {
    music: {
      title: '🎵  Music Commands',
      color: C.primary,
      fields: [
        { name: '▶️ Play',          value: '`-play <query/URL>` `-p <query>` — Play from YouTube or Spotify' },
        { name: '⏸ Pause/Resume',  value: '`-pause` `-resume`' },
        { name: '⏭ Skip',          value: '`-skip` `-s` — Skip current track' },
        { name: '⏮ Back',          value: '`-back` `-b` `-prev` — Go to previous track' },
        { name: '⏩ Forward',       value: '`-forward [secs]` — Fast-forward (default 10s)' },
        { name: '⏪ Rewind',        value: '`-rewind [secs]` — Rewind (default 10s)' },
        { name: '🎯 Seek',          value: '`-seek <mm:ss>` — Seek to timestamp' },
        { name: '⏹ Stop',          value: '`-stop` — Stop & clear queue' },
        { name: '🔊 Volume',        value: '`-volume <1–200>` `-v <1–200>`' },
        { name: '🎵 Now Playing',   value: '`-nowplaying` `-np`' },
        { name: '🎤 Lyrics',        value: '`-lyrics [song]` — Get song lyrics' },
        { name: '👋 Leave',         value: '`-leave` `-dc` — Disconnect bot' },
      ],
    },
    queue: {
      title: '📋  Queue Commands',
      color: C.info,
      fields: [
        { name: '📋 View Queue',    value: '`-queue [page]` `-q [page]`' },
        { name: '🔀 Shuffle',       value: '`-shuffle` — Shuffle the queue' },
        { name: '🔁 Loop',          value: '`-loop` — Cycle: Off → Track → Queue' },
        { name: '♾️ Autoplay',      value: '`-autoplay` — Auto-add related songs' },
        { name: '⏭ Skip To',       value: '`-skipto <pos>` — Jump to position' },
        { name: '🗑 Remove',        value: '`-remove <pos>` — Remove a track' },
        { name: '↕️ Move',          value: '`-move <from> <to>` — Reorder track' },
        { name: '🧹 Clear',         value: '`-clear` — Clear queue (keeps current)' },
      ],
    },
    playlist: {
      title: '📁  Playlist Commands',
      color: C.success,
      fields: [
        { name: '📁 Create',        value: '`-pl create <name>` — Create a playlist' },
        { name: '🗑 Delete',        value: '`-pl delete <name>`' },
        { name: '📋 List',          value: '`-pl list` — All your playlists' },
        { name: '👁 View',          value: '`-pl view <name>` — See playlist songs' },
        { name: '➕ Add Song',      value: '`-pl add <name>` — Add current song' },
        { name: '➖ Remove Song',   value: '`-pl remove <name> <pos>`' },
        { name: '▶️ Play',          value: '`-pl play <name>` — Queue entire playlist' },
        { name: '✏️ Rename',        value: '`-pl rename <old> <new>`' },
      ],
    },
    liked: {
      title: '❤️  Liked Songs',
      color: C.error,
      fields: [
        { name: '❤️ Like',          value: '`-like` — Like currently playing song' },
        { name: '💔 Unlike',        value: '`-unlike` — Unlike current song' },
        { name: '📋 View',          value: '`-liked` — View all liked songs' },
        { name: '▶️ Play All',      value: '`-liked play` — Queue all liked songs' },
      ],
    },
    premium: {
      title: '⭐  Premium Commands',
      color: C.premium,
      fields: [
        { name: '🎛️ Filters',       value: '`-filter <name>` — Apply audio filter\nAvailable: `bass` `8d` `nightcore` `vaporwave` `tremolo` `vibrato` `normalizer` `reset`' },
        { name: '🔒 24/7 Mode',     value: '`-247` — Bot stays in VC permanently' },
        { name: '🎧 DJ Role',       value: '`-djrole [@role]` — Set/clear DJ role' },
        { name: '📊 Status',        value: '`-premium` — Check premium status' },
        { name: '🗳️ Vote',          value: '`-vote` — Vote on Top.gg for 12hr premium' },
        { name: '\u200B',           value: '> Get **Server Premium** by contacting the bot owner.\n> Get **12hr Premium** by voting on Top.gg!' },
      ],
    },
    owner: {
      title: '👑  Owner Commands',
      color: C.warning,
      fields: [
        { name: '⭐ Grant Premium', value: '`-premium grant <guildId>`' },
        { name: '❌ Revoke Premium',value: '`-premium revoke <guildId>`' },
        { name: '📋 List Premium',  value: '`-premium list`' },
        { name: '📊 Guild Info',    value: '`-premium status <guildId>`' },
        { name: '📢 Set Status',    value: '`-setstatus <text>`' },
        { name: '💻 Eval',          value: '`-eval <code>` — Run JS (owner only)' },
      ],
    },
  };

  const d = data[cat];
  if (!d) return null;

  return new EmbedBuilder()
    .setColor(d.color)
    .setTitle(d.title)
    .addFields(d.fields)
    .setFooter({ text: 'Zero Music • Made by Aditya</>  •  Use the menu to switch categories' });
}

// ─── BACK BUTTON ROW ─────────────────────────────────────────────────────────
function backButton() {
  return new ActionRowBuilder().addComponents(
    new ButtonBuilder().setCustomId('help_back').setLabel('← Back to Menu').setStyle(ButtonStyle.Secondary)
  );
}

module.exports = {
  nowPlaying, addedToQueue, queueEmbed,
  err, ok, info,
  premiumWall, aboutEmbed,
  helpMain, helpCategory, backButton,
  progressBar, footer,
};
