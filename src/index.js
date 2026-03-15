import {
  Client,
  Collection,
  GatewayIntentBits,
  Partials,
  Events
} from "discord.js";
import { REST } from "@discordjs/rest";
import { Routes } from "discord-api-types/v10";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { DEFAULT_PREFIX, DISCORD_TOKEN, DISCORD_CLIENT_ID, DISCORD_GUILD_ID, OWNER_ID } from "./config.js";
import { createPlayer } from "./music/player.js";
import { startTopggWebhook } from "./topgg/webhook.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

if (!DISCORD_TOKEN || !DISCORD_CLIENT_ID) {
  console.error("DISCORD_TOKEN or DISCORD_CLIENT_ID missing in environment. Check your .env.");
  process.exit(1);
}

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.GuildVoiceStates,
    GatewayIntentBits.MessageContent
  ],
  partials: [Partials.Channel]
});

client.commands = new Collection();
client.slashCommands = [];
client.prefix = DEFAULT_PREFIX;

// Load command modules
const commandsPath = path.join(__dirname, "modules");
if (!fs.existsSync(commandsPath)) {
  fs.mkdirSync(commandsPath, { recursive: true });
}

const commandFolders = fs.readdirSync(commandsPath).filter((file) =>
  fs.statSync(path.join(commandsPath, file)).isDirectory()
);

for (const folder of commandFolders) {
  const folderPath = path.join(commandsPath, folder);
  const commandFiles = fs
    .readdirSync(folderPath)
    .filter((file) => file.endsWith(".js"));

  for (const file of commandFiles) {
    const filePath = path.join(folderPath, file);
    const command = (await import(filePath)).default;
    if (!command) continue;

    if (command.data && command.data.name) {
      // slash command
      client.slashCommands.push(command.data.toJSON());
    }

    if (command.name) {
      client.commands.set(command.name, command);
    }
  }
}

// Register slash commands
const rest = new REST({ version: "10" }).setToken(DISCORD_TOKEN);

async function registerSlashCommands() {
  try {
    if (DISCORD_GUILD_ID) {
      await rest.put(
        Routes.applicationGuildCommands(DISCORD_CLIENT_ID, DISCORD_GUILD_ID),
        { body: client.slashCommands }
      );
      console.log("✅ Registered guild slash commands.");
    } else {
      await rest.put(Routes.applicationCommands(DISCORD_CLIENT_ID), {
        body: client.slashCommands
      });
      console.log("✅ Registered global slash commands (may take up to 1 hour to appear).");
    }
  } catch (error) {
    console.error("Error registering slash commands:", error);
  }
}

// Attach music player
const player = await createPlayer(client);
client.player = player;

client.once(Events.ClientReady, async (readyClient) => {
  console.log(`✅ Logged in as ${readyClient.user.tag}`);
  await registerSlashCommands();
  startTopggWebhook();
  client.user.setPresence({
    activities: [{ name: "/play | -help", type: 2 }],
    status: "online"
  });
});

client.on(Events.InteractionCreate, async (interaction) => {
  if (!interaction.isChatInputCommand()) return;

  const command = client.commands.get(interaction.commandName);
  if (!command) return;

  try {
    await command.executeSlash(interaction, client);
  } catch (error) {
    console.error(error);
    if (interaction.replied || interaction.deferred) {
      await interaction.followUp({
        content: "There was an error while executing this command.",
        ephemeral: true
      });
    } else {
      await interaction.reply({
        content: "There was an error while executing this command.",
        ephemeral: true
      });
    }
  }
});

client.on(Events.MessageCreate, async (message) => {
  if (message.author.bot || !message.guild) return;

  const prefix = client.prefix;
  if (!message.content.startsWith(prefix)) return;

  const args = message.content.slice(prefix.length).trim().split(/\s+/);
  const commandName = args.shift().toLowerCase();

  const command =
    client.commands.get(commandName) ||
    client.commands.find(
      (cmd) => cmd.aliases && cmd.aliases.includes(commandName)
    );

  if (!command || !command.executePrefix) return;

  try {
    await command.executePrefix(message, args, client);
  } catch (error) {
    console.error(error);
    message.reply("There was an error while executing this command.").catch(() => {});
  }
});

client.on(Events.Error, (error) => {
  console.error("Discord client error:", error);
});

client.login(DISCORD_TOKEN);

