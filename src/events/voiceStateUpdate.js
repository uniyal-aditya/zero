const db = require('../utils/database');

module.exports = {
  name: 'voiceStateUpdate',
  async execute(oldState, newState, client) {
    // If the bot itself was disconnected and 24/7 is on → rejoin
    if (oldState.member?.id !== client.user.id) return;
    if (newState.channelId) return; // moved, not disconnected

    const guildId  = oldState.guild.id;
    const settings = db.getSettings(guildId);
    if (!settings.tfSeven) return;

    const queue = client.player.nodes.get(guildId);
    if (!queue || !queue.channel) return;

    setTimeout(() => {
      queue.channel.join?.().catch(() => {});
    }, 1500);
  },
};
