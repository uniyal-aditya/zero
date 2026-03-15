const { useQueue } = require('discord-player');
const { ctx } = require('../../utils/ctx');
const E       = require('../../utils/embeds');

module.exports = {
  name: 'queue',
  aliases: ['q'],
  description: 'Show the music queue',
  async execute(msg, args, client, isSlash = false) {
    const c = ctx(msg, isSlash);
    const q = useQueue(c.guildId);
    if (!q || (!q.currentTrack && q.tracks.size === 0))
      return c.reply({ embeds: [E.err('The queue is empty!')] });
    const page = isSlash ? (msg.options.getInteger('page') ?? 1) : (parseInt(args[0]) || 1);
    return c.reply({ embeds: [E.queueEmbed(q, page)] });
  },
};
