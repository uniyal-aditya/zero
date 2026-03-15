const { ctx }  = require('../../utils/ctx');
const E        = require('../../utils/embeds');

module.exports = {
  name: 'help',
  aliases: ['h', 'commands', 'cmds'],
  description: 'Interactive help menu',
  async execute(msg, args, client, isSlash = false) {
    const c   = ctx(msg, isSlash);
    const cat = isSlash ? msg.options.getString('category') : args[0]?.toLowerCase();

    if (cat) {
      const embed = E.helpCategory(cat);
      if (!embed) return c.reply({ embeds: [E.err('Unknown category. Valid: `music` `queue` `playlist` `liked` `premium` `owner`')] });
      return c.reply({ embeds: [embed], components: [E.backButton()] });
    }

    const { embed, menu } = E.helpMain(client);
    return c.reply({ embeds: [embed], components: [menu] });
  },
};
