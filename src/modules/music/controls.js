import { SlashCommandBuilder } from "discord.js";

const nowplayingData = new SlashCommandBuilder()
  .setName("nowplaying")
  .setDescription("Show the currently playing track.");

const skipData = new SlashCommandBuilder()
  .setName("skip")
  .setDescription("Skip the current track.");

const backData = new SlashCommandBuilder()
  .setName("back")
  .setDescription("Go back to the previous track.");

const pauseData = new SlashCommandBuilder()
  .setName("pause")
  .setDescription("Pause the current track.");

const resumeData = new SlashCommandBuilder()
  .setName("resume")
  .setDescription("Resume the current track.");

const stopData = new SlashCommandBuilder()
  .setName("stop")
  .setDescription("Stop playback and clear the queue.");

const shuffleData = new SlashCommandBuilder()
  .setName("shuffle")
  .setDescription("Shuffle the current queue.");

const loopData = new SlashCommandBuilder()
  .setName("loop")
  .setDescription("Set loop mode.")
  .addStringOption((o) =>
    o
      .setName("mode")
      .setDescription("off / track / queue / autoplay")
      .setRequired(true)
      .addChoices(
        { name: "off", value: "off" },
        { name: "track", value: "track" },
        { name: "queue", value: "queue" },
        { name: "autoplay", value: "autoplay" }
      )
  );

const queueData = new SlashCommandBuilder()
  .setName("queue")
  .setDescription("Show the current queue.");

const commands = [];

function makeHandler(name, handler) {
  const cmd = {
    name,
    data:
      name === "nowplaying"
        ? nowplayingData
        : name === "skip"
        ? skipData
        : name === "back"
        ? backData
        : name === "pause"
        ? pauseData
        : name === "resume"
        ? resumeData
        : name === "stop"
        ? stopData
        : name === "shuffle"
        ? shuffleData
        : name === "loop"
        ? loopData
        : queueData,
    async executeSlash(interaction, client) {
      await handler({ type: "slash", interaction, client });
    },
    async executePrefix(message, args, client) {
      await handler({ type: "prefix", message, client, args });
    }
  };

  commands.push(cmd);
  return cmd;
}

function getQueueOrReply(ctx) {
  const isSlash = ctx.type === "slash";
  const interaction = ctx.interaction;
  const message = ctx.message;
  const client = ctx.client;

  const guild = isSlash ? interaction.guild : message.guild;
  const queue = client.player.nodes.get(guild.id);

  if (!queue || !queue.node.isPlaying()) {
    const content = "Nothing is playing right now.";
    if (isSlash) {
      interaction.reply({ content, ephemeral: true }).catch(() => {});
    } else {
      message.reply(content).catch(() => {});
    }
    return null;
  }
  return queue;
}

makeHandler("nowplaying", async (ctx) => {
  const isSlash = ctx.type === "slash";
  const interaction = ctx.interaction;
  const message = ctx.message;

  const queue = getQueueOrReply(ctx);
  if (!queue) return;

  const track = queue.currentTrack;
  const content = `🎵 Now playing: **${track.title}** \`[${track.duration}]\``;
  if (isSlash) {
    await interaction.reply({ content });
  } else {
    await message.channel.send(content).catch(() => {});
  }
});

makeHandler("skip", async (ctx) => {
  const isSlash = ctx.type === "slash";
  const interaction = ctx.interaction;
  const message = ctx.message;

  const queue = getQueueOrReply(ctx);
  if (!queue) return;

  await queue.node.skip();
  const content = "⏭ Skipped.";
  if (isSlash) {
    await interaction.reply({ content });
  } else {
    await message.channel.send(content).catch(() => {});
  }
});

makeHandler("back", async (ctx) => {
  const isSlash = ctx.type === "slash";
  const interaction = ctx.interaction;
  const message = ctx.message;

  const queue = getQueueOrReply(ctx);
  if (!queue) return;

  const success = await queue.history.previous();
  const content = success ? "⏮ Going back to previous track." : "No previous track in history.";
  if (isSlash) {
    await interaction.reply({ content });
  } else {
    await message.channel.send(content).catch(() => {});
  }
});

makeHandler("pause", async (ctx) => {
  const isSlash = ctx.type === "slash";
  const interaction = ctx.interaction;
  const message = ctx.message;

  const queue = getQueueOrReply(ctx);
  if (!queue) return;

  queue.node.setPaused(true);
  const content = "⏸ Paused.";
  if (isSlash) {
    await interaction.reply({ content });
  } else {
    await message.channel.send(content).catch(() => {});
  }
});

makeHandler("resume", async (ctx) => {
  const isSlash = ctx.type === "slash";
  const interaction = ctx.interaction;
  const message = ctx.message;

  const queue = getQueueOrReply(ctx);
  if (!queue) return;

  queue.node.setPaused(false);
  const content = "▶️ Resumed.";
  if (isSlash) {
    await interaction.reply({ content });
  } else {
    await message.channel.send(content).catch(() => {});
  }
});

makeHandler("stop", async (ctx) => {
  const isSlash = ctx.type === "slash";
  const interaction = ctx.interaction;
  const message = ctx.message;

  const queue = getQueueOrReply(ctx);
  if (!queue) return;

  queue.delete();
  const content = "⏹ Stopped and cleared the queue.";
  if (isSlash) {
    await interaction.reply({ content });
  } else {
    await message.channel.send(content).catch(() => {});
  }
});

makeHandler("shuffle", async (ctx) => {
  const isSlash = ctx.type === "slash";
  const interaction = ctx.interaction;
  const message = ctx.message;

  const queue = getQueueOrReply(ctx);
  if (!queue) return;

  queue.tracks.shuffle();
  const content = "🔀 Shuffled the queue.";
  if (isSlash) {
    await interaction.reply({ content });
  } else {
    await message.channel.send(content).catch(() => {});
  }
});

makeHandler("loop", async (ctx) => {
  const isSlash = ctx.type === "slash";
  const interaction = ctx.interaction;
  const message = ctx.message;

  const queue = getQueueOrReply(ctx);
  if (!queue) return;

  const mode = isSlash
    ? interaction.options.getString("mode", true)
    : (ctx.args[0] || "off");

  switch (mode) {
    case "off":
      queue.setRepeatMode(0);
      queue.setAutoplay(false);
      break;
    case "track":
      queue.setRepeatMode(1);
      queue.setAutoplay(false);
      break;
    case "queue":
      queue.setRepeatMode(2);
      queue.setAutoplay(false);
      break;
    case "autoplay":
      queue.setAutoplay(true);
      break;
    default:
      {
        const content = "Invalid loop mode. Use off / track / queue / autoplay.";
        if (isSlash) {
          await interaction.reply({ content, ephemeral: true });
        } else {
          await message.reply(content).catch(() => {});
        }
      }
      return;
  }

  const content = `Loop mode set to **${mode}**.`;
  if (isSlash) {
    await interaction.reply({ content });
  } else {
    await message.channel.send(content).catch(() => {});
  }
});

makeHandler("queue", async (ctx) => {
  const isSlash = ctx.type === "slash";
  const interaction = ctx.interaction;
  const message = ctx.message;

  const queue = getQueueOrReply(ctx);
  if (!queue) return;

  const tracks = queue.tracks.toArray();
  const current = queue.currentTrack;

  let description = current
    ? `**Now:** ${current.title} \`[${current.duration}]\`\n\n`
    : "Nothing playing.\n\n";

  if (!tracks.length) {
    description += "Queue is empty.";
  } else {
    const lines = tracks.slice(0, 10).map((t, i) => `${i + 1}. ${t.title} \`[${t.duration}]\``);
    description += lines.join("\n");
    if (tracks.length > 10) {
      description += `\n... and ${tracks.length - 10} more.`;
    }
  }

  const content = description;
  if (isSlash) {
    await interaction.reply({ content });
  } else {
    await message.channel.send(content).catch(() => {});
  }
});

export default commands[0];

