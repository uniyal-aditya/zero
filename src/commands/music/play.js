const { useMainPlayer } = require('discord-player');
const { ctx }  = require('../../utils/ctx');
const E        = require('../../utils/embeds');
const { inVC } = require('../../utils/permissions');
const db       = require('../../utils/database');

module.exports = {
  name: 'play',
  aliases: ['p'],
  description: 'Play a song from YouTube, Spotify, or a search query',

  async execute(msg, args, client, isSlash = false) {
    const c = ctx(msg, isSlash);

    if (!inVC(c.member))
      return c.reply({ embeds: [E.err('You must be in a voice channel!')] });

    const query = isSlash
      ? msg.options.getString('query', true)
      : args.join(' ');

    if (!query)
      return c.reply({ embeds: [E.err('Provide a song name, YouTube link, or Spotify link.')] });

    await c.defer();

    const player = useMainPlayer();
    const settings = db.getSettings(c.guildId);

    try {
      const { track } = await player.play(c.member.voice.channel, query, {
        nodeOptions: {
          metadata: { channel: c.channel, requestedBy: c.user },
          volume: settings.defaultVolume ?? 80,
          selfDeaf: true,
          leaveOnEmpty: !settings.tfSeven,
          leaveOnEmptyCooldown: 30_000,
          leaveOnEnd: !settings.tfSeven,
          leaveOnEndCooldown: 30_000,
        },
        requestedBy: c.user,
      });

      if (isSlash)
        return c.editReply({ embeds: [E.ok(`Queued **${track.title}**`)] });

    } catch (e) {
      console.error('[Play]', e);
      const msg = e.message?.toLowerCase().includes('no results')
        ? 'No results found for that query.'
        : `Could not play: ${e.message}`;
      return c.editReply({ embeds: [E.err(msg)] });
    }
  },
};
