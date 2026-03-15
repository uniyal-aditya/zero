import { SlashCommandBuilder, PermissionFlagsBits } from "discord.js";
import { OWNER_ID } from "../../config.js";
import { grantServerPremium, isGuildPremium, hasActiveVotePremium } from "../../database/premium.js";

const data = new SlashCommandBuilder()
  .setName("premium")
  .setDescription("Premium status and controls.")
  .addSubcommand((sub) =>
    sub
      .setName("status")
      .setDescription("Show this server's premium status.")
  )
  .addSubcommand((sub) =>
    sub
      .setName("grant")
      .setDescription("Grant permanent premium to this server (bot owner only).")
      .setDefaultMemberPermissions(PermissionFlagsBits.Administrator)
  );

const command = {
  name: "premium",
  data,
  async executeSlash(interaction) {
    const sub = interaction.options.getSubcommand();

    if (sub === "status") {
      const guildId = interaction.guild.id;
      const userId = interaction.user.id;
      const guildPremium = isGuildPremium(guildId);
      const votePremium = hasActiveVotePremium(userId);

      let content = `**Premium status for ${interaction.guild.name}:**\n`;
      content += guildPremium ? "- Server premium: **Active**\n" : "- Server premium: Inactive\n";
      content += votePremium ? "- Your vote premium: **Active (12h window)**\n" : "- Your vote premium: Inactive\n";

      content += "\nPremium-only commands will work if either server premium or your vote premium is active.";

      await interaction.reply({ content, ephemeral: true });
    } else if (sub === "grant") {
      if (interaction.user.id !== OWNER_ID) {
        return interaction.reply({
          content: "Only the bot owner can grant permanent premium.",
          ephemeral: true
        });
      }

      const guildId = interaction.guild.id;
      grantServerPremium(guildId, interaction.user.id);

      await interaction.reply({
        content: "✅ Permanent premium granted to this server.",
        ephemeral: false
      });
    }
  },
  async executePrefix(message, args) {
    const sub = (args[0] || "status").toLowerCase();

    if (sub === "status") {
      const guildId = message.guild.id;
      const userId = message.author.id;
      const guildPremium = isGuildPremium(guildId);
      const votePremium = hasActiveVotePremium(userId);

      let content = `**Premium status for ${message.guild.name}:**\n`;
      content += guildPremium ? "- Server premium: **Active**\n" : "- Server premium: Inactive\n";
      content += votePremium ? "- Your vote premium: **Active (12h window)**\n" : "- Your vote premium: Inactive\n";

      await message.reply(content).catch(() => {});
    } else if (sub === "grant") {
      if (message.author.id !== OWNER_ID) {
        return message.reply("Only the bot owner can grant permanent premium.").catch(() => {});
      }

      const guildId = message.guild.id;
      grantServerPremium(guildId, message.author.id);
      await message.reply("✅ Permanent premium granted to this server.").catch(() => {});
    }
  }
};

export default command;

