const Embeds = require('../utils/embeds');

module.exports = {
  name: 'interactionCreate',
  async execute(interaction, client) {

    // ── SLASH COMMANDS ────────────────────────────────────────────────────────
    if (interaction.isChatInputCommand()) {
      const cmd = client.commands.get(interaction.commandName);
      if (!cmd) return;
      try {
        await cmd.execute(interaction, [], client, true);
      } catch (e) {
        console.error('[Slash Error]', e);
        const payload = { embeds: [Embeds.err('An error occurred.')], ephemeral: true };
        interaction.replied || interaction.deferred
          ? interaction.followUp(payload).catch(() => {})
          : interaction.reply(payload).catch(() => {});
      }
      return;
    }

    // ── HELP SELECT MENU ──────────────────────────────────────────────────────
    if (interaction.isStringSelectMenu() && interaction.customId === 'help_menu') {
      const cat   = interaction.values[0];
      const embed = Embeds.helpCategory(cat);
      if (!embed) return interaction.reply({ embeds: [Embeds.err('Unknown category.')], ephemeral: true });
      await interaction.update({ embeds: [embed], components: [Embeds.backButton()] });
      return;
    }

    // ── BACK BUTTON ───────────────────────────────────────────────────────────
    if (interaction.isButton() && interaction.customId === 'help_back') {
      const { embed, menu } = Embeds.helpMain(client);
      await interaction.update({ embeds: [embed], components: [menu] });
      return;
    }
  },
};
