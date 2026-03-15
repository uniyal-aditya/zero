const { useQueue } = require('discord-player');
const { EmbedBuilder } = require('discord.js');
const { ctx }                      = require('../../utils/ctx');
const E                            = require('../../utils/embeds');
const db                           = require('../../utils/database');
const { isOwner, hasPremium, inVC } = require('../../utils/permissions');
const { hasVoted }                  = require('../../utils/topgg');
const cfg                           = require('../../config');

// ── FILTER ────────────────────────────────────────────────────────────────────
const filter = {
  name: 'filter',
  aliases: ['filters', 'fx'],
  description: 'Apply an audio filter (Premium)',
  async execute(msg, args, client, isSlash = false) {
    const c = ctx(msg, isSlash);
    if (!hasPremium(c.guildId, c.user.id)) return c.reply({ embeds: [E.premiumWall()] });
    if (!inVC(c.member)) return c.reply({ embeds: [E.err('You must be in a voice channel!')] });
    const q = useQueue(c.guildId);
    if (!q?.currentTrack) return c.reply({ embeds: [E.err('Nothing is playing!')] });

    const name = (isSlash ? msg.options.getString('name') : args[0])?.toLowerCase();
    const valid = ['bass', '8d', 'nightcore', 'vaporwave', 'tremolo', 'vibrato', 'normalizer', 'fadein', 'reverse', 'reset'];

    if (!name || !valid.includes(name)) {
      return c.reply({
        embeds: [new EmbedBuilder()
          .setColor(cfg.colors.premium)
          .setTitle('🎛️  Audio Filters')
          .setDescription(valid.filter(f => f !== 'reset').map(f => `\`${f}\``).join('  '))
          .addFields({ name: 'Usage', value: '`-filter <name>`  •  `-filter reset` to clear' })
          .setFooter({ text: 'Zero Music • Made by Aditya</>' })],
      });
    }

    if (name === 'reset') {
      await q.filters.ffmpeg.setFilters(false);
      return c.reply({ embeds: [E.ok('🎵 All filters removed.')] });
    }

    const map = {
      bass:       { bassboost_high: true },
      '8d':       { '8d': true },
      nightcore:  { nightcore: true },
      vaporwave:  { vaporwave: true },
      tremolo:    { tremolo: true },
      vibrato:    { vibrato: true },
      normalizer: { normalizer: true },
      fadein:     { fadein: true },
      reverse:    { reverse: true },
    };
    await q.filters.ffmpeg.setFilters(map[name]);
    return c.reply({ embeds: [E.ok(`🎛️ Applied **${name}** filter.`)] });
  },
};

// ── 24/7 ──────────────────────────────────────────────────────────────────────
const tfSeven = {
  name: '247',
  aliases: ['24/7', 'stay'],
  description: 'Toggle 24/7 mode (Premium)',
  async execute(msg, args, client, isSlash = false) {
    const c = ctx(msg, isSlash);
    if (!hasPremium(c.guildId, c.user.id)) return c.reply({ embeds: [E.premiumWall()] });
    if (!c.member.permissions.has('ManageGuild') && !isOwner(c.user.id))
      return c.reply({ embeds: [E.err('You need **Manage Server** permission.')] });
    const current = db.getSettings(c.guildId).tfSeven;
    db.setSetting(c.guildId, 'tfSeven', !current);
    return c.reply({ embeds: [E.ok(!current
      ? '🔒 **24/7 Mode ON** — I\'ll stay in voice even when the queue ends!'
      : '🔓 **24/7 Mode OFF** — I\'ll leave when the queue is empty.')] });
  },
};

// ── DJ ROLE ───────────────────────────────────────────────────────────────────
const djrole = {
  name: 'djrole',
  description: 'Set or clear the DJ role (Premium)',
  async execute(msg, args, client, isSlash = false) {
    const c = ctx(msg, isSlash);
    if (!hasPremium(c.guildId, c.user.id)) return c.reply({ embeds: [E.premiumWall()] });
    if (!c.member.permissions.has('ManageGuild') && !isOwner(c.user.id))
      return c.reply({ embeds: [E.err('You need **Manage Server** permission.')] });

    const role = isSlash
      ? msg.options.getRole('role')
      : msg.mentions?.roles?.first();

    if (!role) {
      db.setSetting(c.guildId, 'djRole', null);
      return c.reply({ embeds: [E.ok('🎧 DJ role cleared. Everyone can control music.')] });
    }
    db.setSetting(c.guildId, 'djRole', role.id);
    return c.reply({ embeds: [E.ok(`🎧 **${role.name}** set as the DJ role.`)] });
  },
};

// ── VOTE ──────────────────────────────────────────────────────────────────────
const vote = {
  name: 'vote',
  description: 'Vote for Zero on Top.gg for 12 hours of Premium',
  async execute(msg, args, client, isSlash = false) {
    const c = ctx(msg, isSlash);
    await c.defer();
    const uid = c.user.id;

    // Already has active vote premium?
    if (db.hasVotePremium(uid)) {
      const mins = Math.ceil((db.getVoteExpiry(uid) - Date.now()) / 60_000);
      return c.editReply({
        embeds: [new EmbedBuilder()
          .setColor(cfg.colors.premium)
          .setTitle('⭐  Vote Premium Active')
          .setDescription(`You already have vote premium!\n**Expires in:** ${mins} minute${mins !== 1 ? 's' : ''}`)
          .setFooter({ text: 'Zero Music • Made by Aditya</>' })],
      });
    }

    const voted = await hasVoted(uid);
    if (voted) {
      db.grantVotePremium(uid);
      return c.editReply({
        embeds: [new EmbedBuilder()
          .setColor(cfg.colors.premium)
          .setTitle('✅  Vote Premium Granted!')
          .setDescription(
            `Thanks for voting! You now have **12 hours** of Premium!\n\n` +
            `**Unlocked features:**\n${cfg.premiumFeatures.map(f => `• ${f}`).join('\n')}`
          )
          .setFooter({ text: 'Zero Music • Vote again after 12h to renew • Made by Aditya</>' })],
      });
    }

    // Not voted yet
    return c.editReply({
      embeds: [new EmbedBuilder()
        .setColor(cfg.colors.info)
        .setTitle('🗳️  Vote for Zero!')
        .setDescription(
          `Vote for **Zero** on Top.gg to get **12 hours of free Premium**!\n\n` +
          `**[👉 Click here to vote](https://top.gg/bot/${cfg.topggBotId}/vote)**\n\n` +
          `After voting, run \`-vote\` again to claim your reward.`
        )
        .addFields({ name: '⭐ What you get', value: cfg.premiumFeatures.map(f => `• ${f}`).join('\n') })
        .setFooter({ text: 'Zero Music • Made by Aditya</>' })],
    });
  },
};

// ── PREMIUM (status + owner management) ──────────────────────────────────────
const premium = {
  name: 'premium',
  aliases: ['prem'],
  description: 'Check premium status or manage it (owner)',
  async execute(msg, args, client, isSlash = false) {
    const c   = ctx(msg, isSlash);
    const uid = c.user.id;
    const sub = args[0]?.toLowerCase();

    // ── OWNER SUBCOMMANDS ────────────────────────────────────────────────────
    if (isOwner(uid)) {
      if (sub === 'grant') {
        const gId = args[1];
        if (!gId) return c.reply({ embeds: [E.err('Provide a guild ID.')] });
        db.grantPremium(gId, uid);
        return c.reply({ embeds: [E.ok(`⭐ Granted premium to server \`${gId}\`.`)] });
      }
      if (sub === 'revoke') {
        const gId = args[1];
        if (!gId) return c.reply({ embeds: [E.err('Provide a guild ID.')] });
        db.revokePremium(gId);
        return c.reply({ embeds: [E.ok(`❌ Revoked premium from \`${gId}\`.`)] });
      }
      if (sub === 'list') {
        const guilds = db.getAllPremiumGuilds();
        return c.reply({
          embeds: [new EmbedBuilder()
            .setColor(cfg.colors.premium)
            .setTitle('👑  Premium Servers')
            .setDescription(guilds.length ? guilds.map((g, i) => `${i + 1}. \`${g}\``).join('\n') : 'None.')
            .setFooter({ text: `${guilds.length} server(s) • Made by Aditya</>` })],
        });
      }
      if (sub === 'status' && args[1]) {
        const info = db.getPremiumInfo(args[1]);
        return c.reply({
          embeds: [new EmbedBuilder()
            .setColor(info?.active ? cfg.colors.premium : cfg.colors.error)
            .setTitle(`Server \`${args[1]}\` Premium`)
            .addFields(
              { name: 'Status',    value: info?.active ? '✅ Active' : '❌ Inactive', inline: true },
              { name: 'Granted by',value: info?.grantedBy ?? 'N/A',                  inline: true },
              { name: 'Since',     value: info?.grantedAt ? `<t:${Math.floor(info.grantedAt / 1000)}:R>` : 'N/A', inline: true },
            )
            .setFooter({ text: 'Zero Music • Made by Aditya</>' })],
        });
      }
    }

    // ── USER STATUS ──────────────────────────────────────────────────────────
    const serverPrem = db.isPremiumGuild(c.guildId);
    const votePrem   = db.hasVotePremium(uid);
    const expiry     = db.getVoteExpiry(uid);

    return c.reply({
      embeds: [new EmbedBuilder()
        .setColor(serverPrem || votePrem ? cfg.colors.premium : cfg.colors.info)
        .setTitle('⭐  Zero Premium Status')
        .addFields(
          { name: '🏠 Server Premium', value: serverPrem ? '✅ Active' : '❌ Not active', inline: true },
          { name: '🗳️ Vote Premium',   value: votePrem ? `✅ Active (<t:${Math.floor((expiry ?? 0) / 1000)}:R>)` : '❌ Not active', inline: true },
        )
        .addFields({ name: 'How to get Premium',
          value: `• [Vote on Top.gg](https://top.gg/bot/${cfg.topggBotId}/vote) → 12hr free\n• Contact bot owner to grant server premium` })
        .setFooter({ text: 'Zero Music • Made by Aditya</>' })],
    });
  },
};

module.exports = { filter, tfSeven, djrole, vote, premium };
