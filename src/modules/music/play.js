import { SlashCommandBuilder } from "discord.js";

const data = new SlashCommandBuilder()
  .setName("play")
  .setDescription("Play a song from YouTube or Spotify (alias: /p).")
  .addStringOption((option) =>
    option
      .setName("query")
      .setDescription("YouTube/Spotify link or search terms")
      .setRequired(true)
  );

const command = {
  name: "play",
  aliases: ["p"],
  data,
  async executeSlash(interaction, client) {
    const query = interaction.options.getString("query", true);
    await handlePlay({ type: "slash", interaction, client, query });
  },
  async executePrefix(message, args, client) {
    const query = args.join(" ");
    if (!query) {
      return message.reply("Please provide a search query or link.").catch(() => {});
    }
    await handlePlay({ type: "prefix", message, client, query });
  }
};

async function handlePlay(ctx) {
  const isSlash = ctx.type === "slash";
  const interaction = ctx.interaction;
  const message = ctx.message;
  const client = ctx.client;
  const query = ctx.query;

  const member = (isSlash ? interaction.member : message.member);
  const voiceChannel = member?.voice?.channel;

  if (!voiceChannel) {
    const content = "You need to join a voice channel first.";
    if (isSlash) {
      return interaction.reply({ content, ephemeral: true });
    } else {
      return message.reply(content).catch(() => {});
    }
  }

  if (isSlash) {
    await interaction.deferReply();
  }

  const queue = client.player.nodes.create(voiceChannel.guild, {
    metadata: {
      channel: isSlash ? interaction.channel : message.channel
    },
    selfDeaf: true,
    volume: 80
  });

  try {
    if (!queue.connection) await queue.connect(voiceChannel);
  } catch (error) {
    console.error(error);
    queue.delete();
    const content = "I couldn't join your voice channel.";
    if (isSlash) {
      return interaction.editReply({ content });
    } else {
      return message.reply(content).catch(() => {});
    }
  }

  try {
    const result = await client.player.search(query, {
      requestedBy: isSlash ? interaction.user : message.author
    });

    if (!result.hasTracks()) {
      const content = "No results found.";
      if (isSlash) {
        return interaction.editReply({ content });
      } else {
        return message.reply(content).catch(() => {});
      }
    }

    if (result.playlist) {
      await queue.addTrack(result.tracks);
    } else {
      await queue.addTrack(result.tracks[0]);
    }

    if (!queue.node.isPlaying()) await queue.node.play();

    const content = result.playlist
      ? `Queued **${result.tracks.length}** tracks from playlist **${result.playlist.title}**.`
      : `Queued **${result.tracks[0].title}**.`;

    if (isSlash) {
      await interaction.editReply({ content });
    } else {
      await message.channel.send(content).catch(() => {});
    }
  } catch (error) {
    console.error(error);
    const content = "There was an error while trying to play that track.";
    if (isSlash) {
      if (interaction.deferred) {
        await interaction.editReply({ content });
      } else {
        await interaction.reply({ content, ephemeral: true });
      }
    } else {
      await message.reply(content).catch(() => {});
    }
  }
}

export default command;

