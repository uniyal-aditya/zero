const { useQueue } = require('discord-player');
const { EmbedBuilder } = require('discord.js');
const { ctx } = require('../../utils/ctx');
const E       = require('../../utils/embeds');

module.exports = {
  name: 'lyrics',
  description: 'Get lyrics for the current or a named song',
  async execute(msg, args, client, isSlash = false) {
    const c     = ctx(msg, isSlash);
    const q     = useQueue(c.guildId);
    const query = isSlash
      ? (msg.options.getString('query') ?? q?.currentTrack?.title)
      : (args.join(' ')               || q?.currentTrack?.title);

    if (!query)
      return c.reply({ embeds: [E.err('Nothing is playing and no query was given.')] });

    await c.defer();

    try {
      const Genius  = require('genius-lyrics');
      const Client  = new Genius.Client();
      const results = await Client.songs.search(query);
      if (!results.length)
        return c.editReply({ embeds: [E.err(`No lyrics found for **${query}**.`)] });

      const lyrics = await results[0].lyrics();
      if (!lyrics)
        return c.editReply({ embeds: [E.err(`Lyrics unavailable for **${query}**.`)] });

      // Split into 4000-char chunks
      const chunks = lyrics.match(/[\s\S]{1,4000}/g) ?? [];
      const first  = new EmbedBuilder()
        .setColor(0x5865F2)
        .setTitle(`🎤  ${results[0].title}`)
        .setDescription(chunks[0])
        .setFooter({ text: `Artist: ${results[0].artist.name} • Made by Aditya</>` });

      await c.editReply({ embeds: [first] });
      for (let i = 1; i < Math.min(chunks.length, 3); i++) {
        await c.raw.followUp?.({ embeds: [new EmbedBuilder().setColor(0x5865F2).setDescription(chunks[i])] });
      }
    } catch (e) {
      console.error('[Lyrics]', e);
      return c.editReply({ embeds: [E.err('Could not fetch lyrics.')] });
    }
  },
};
