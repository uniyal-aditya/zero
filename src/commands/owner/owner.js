const { ActivityType } = require('discord.js');
const { ctx }        = require('../../utils/ctx');
const E              = require('../../utils/embeds');
const { isOwner }    = require('../../utils/permissions');

function ownerOnly(c) {
  if (!isOwner(c.user.id))
    return c.reply({ embeds: [E.err('This command is restricted to the bot owner.')] });
  return null;
}

// ── EVAL ──────────────────────────────────────────────────────────────────────
const evalCmd = {
  name: 'eval',
  description: 'Evaluate JavaScript (owner only)',
  async execute(msg, args, client, isSlash = false) {
    const c = ctx(msg, isSlash);
    const block = ownerOnly(c); if (block) return block;
    const code = args.join(' ');
    if (!code) return c.reply({ embeds: [E.err('Provide code to evaluate.')] });
    try {
      // eslint-disable-next-line no-eval
      let result = eval(code);
      if (result instanceof Promise) result = await result;
      const out = String(result).slice(0, 1900);
      return c.reply({ embeds: [E.info('✅ Eval Result', `\`\`\`js\n${out}\n\`\`\``)] });
    } catch (e) {
      return c.reply({ embeds: [E.err(`\`\`\`js\n${String(e).slice(0, 1900)}\n\`\`\``)] });
    }
  },
};

// ── SET STATUS ────────────────────────────────────────────────────────────────
const setstatus = {
  name: 'setstatus',
  description: 'Set bot status (owner only)',
  async execute(msg, args, client, isSlash = false) {
    const c = ctx(msg, isSlash);
    const block = ownerOnly(c); if (block) return block;
    const text = args.join(' ');
    if (!text) return c.reply({ embeds: [E.err('Provide status text.')] });
    client.user.setActivity(text, { type: ActivityType.Playing });
    return c.reply({ embeds: [E.ok(`✅ Status set to: **${text}**`)] });
  },
};

// ── ANNOUNCE ──────────────────────────────────────────────────────────────────
const announce = {
  name: 'announce',
  description: 'DM all guild owners (owner only)',
  async execute(msg, args, client, isSlash = false) {
    const c = ctx(msg, isSlash);
    const block = ownerOnly(c); if (block) return block;
    const text = args.join(' ');
    if (!text) return c.reply({ embeds: [E.err('Provide an announcement message.')] });
    await c.reply({ embeds: [E.ok(`📢 Sending announcement to ${client.guilds.cache.size} servers…`)] });
    let sent = 0, failed = 0;
    for (const guild of client.guilds.cache.values()) {
      try {
        const owner = await guild.fetchOwner();
        await owner.send(`📢 **Zero Music Announcement**\n\n${text}`);
        sent++;
      } catch { failed++; }
    }
    return c.channel?.send({ embeds: [E.ok(`Sent: **${sent}** ✅  Failed: **${failed}** ❌`)] });
  },
};

module.exports = { evalCmd, setstatus, announce };
