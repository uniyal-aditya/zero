const { E, err } = require('../utils/embeds');
const Embeds = require('../utils/embeds');

module.exports = {
  name: 'messageCreate',
  async execute(message, client) {
    if (message.author.bot || !message.guild) return;

    // ── MENTION TRIGGER: @Zero → send about embed ────────────────────────────
    const mentioned = message.mentions.has(client.user) &&
      !message.content.trim().replace(`<@${client.user.id}>`, '').replace(`<@!${client.user.id}>`, '').trim();

    if (mentioned) {
      return message.reply({
        embeds: [Embeds.aboutEmbed(client, message.author.tag)],
      }).catch(() => {});
    }

    // ── PREFIX COMMANDS ───────────────────────────────────────────────────────
    const prefix = client.config?.prefix ?? '-';
    if (!message.content.startsWith(prefix)) return;

    const args    = message.content.slice(prefix.length).trim().split(/ +/);
    const cmdName = args.shift().toLowerCase();
    if (!cmdName) return;

    const cmd = client.commands.get(cmdName);
    if (!cmd) return;

    try {
      await cmd.execute(message, args, client, false);
    } catch (e) {
      console.error(`[CMD Error] ${cmdName}:`, e);
      message.reply({ embeds: [Embeds.err('An error occurred running that command.')] }).catch(() => {});
    }
  },
};
