require('dotenv').config();
const { REST, Routes, SlashCommandBuilder } = require('discord.js');

const commands = [
  // Music
  new SlashCommandBuilder().setName('play').setDescription('Play a song')
    .addStringOption(o => o.setName('query').setDescription('Song name, YouTube or Spotify URL').setRequired(true)),
  new SlashCommandBuilder().setName('p').setDescription('Play a song (shorthand)')
    .addStringOption(o => o.setName('query').setDescription('Song name, YouTube or Spotify URL').setRequired(true)),
  new SlashCommandBuilder().setName('pause').setDescription('Pause playback'),
  new SlashCommandBuilder().setName('resume').setDescription('Resume playback'),
  new SlashCommandBuilder().setName('skip').setDescription('Skip the current track'),
  new SlashCommandBuilder().setName('back').setDescription('Go back to the previous track'),
  new SlashCommandBuilder().setName('stop').setDescription('Stop music and clear queue'),
  new SlashCommandBuilder().setName('leave').setDescription('Disconnect the bot'),
  new SlashCommandBuilder().setName('nowplaying').setDescription('Show currently playing track'),
  new SlashCommandBuilder().setName('queue').setDescription('Show the music queue')
    .addIntegerOption(o => o.setName('page').setDescription('Page number').setMinValue(1)),
  new SlashCommandBuilder().setName('shuffle').setDescription('Shuffle the queue'),
  new SlashCommandBuilder().setName('loop').setDescription('Cycle through loop modes'),
  new SlashCommandBuilder().setName('autoplay').setDescription('Toggle autoplay'),
  new SlashCommandBuilder().setName('volume').setDescription('Set volume')
    .addIntegerOption(o => o.setName('level').setDescription('1–200').setRequired(true).setMinValue(1).setMaxValue(200)),
  new SlashCommandBuilder().setName('seek').setDescription('Seek to timestamp')
    .addStringOption(o => o.setName('time').setDescription('e.g. 1:30').setRequired(true)),
  new SlashCommandBuilder().setName('forward').setDescription('Fast forward N seconds')
    .addIntegerOption(o => o.setName('seconds').setDescription('Seconds (default 10)').setMinValue(1)),
  new SlashCommandBuilder().setName('rewind').setDescription('Rewind N seconds')
    .addIntegerOption(o => o.setName('seconds').setDescription('Seconds (default 10)').setMinValue(1)),
  new SlashCommandBuilder().setName('skipto').setDescription('Skip to queue position')
    .addIntegerOption(o => o.setName('position').setDescription('Position in queue').setRequired(true).setMinValue(1)),
  new SlashCommandBuilder().setName('remove').setDescription('Remove a song from queue')
    .addIntegerOption(o => o.setName('position').setDescription('Position in queue').setRequired(true).setMinValue(1)),
  new SlashCommandBuilder().setName('move').setDescription('Move a song in queue')
    .addIntegerOption(o => o.setName('from').setDescription('Current position').setRequired(true).setMinValue(1))
    .addIntegerOption(o => o.setName('to').setDescription('New position').setRequired(true).setMinValue(1)),
  new SlashCommandBuilder().setName('clear').setDescription('Clear the queue'),
  new SlashCommandBuilder().setName('lyrics').setDescription('Get song lyrics')
    .addStringOption(o => o.setName('query').setDescription('Song title (defaults to current)')),
  new SlashCommandBuilder().setName('help').setDescription('Show help menu')
    .addStringOption(o => o.setName('category').setDescription('Category').setChoices(
      { name: '🎵 Music',       value: 'music'    },
      { name: '📋 Queue',       value: 'queue'    },
      { name: '📁 Playlists',   value: 'playlist' },
      { name: '❤️ Liked Songs', value: 'liked'    },
      { name: '⭐ Premium',     value: 'premium'  },
    )),

  // Playlist
  new SlashCommandBuilder().setName('pl').setDescription('Manage playlists')
    .addStringOption(o => o.setName('action').setDescription('Action').setRequired(true)
      .setChoices(
        { name: 'create', value: 'create' }, { name: 'delete', value: 'delete' },
        { name: 'list',   value: 'list'   }, { name: 'view',   value: 'view'   },
        { name: 'add',    value: 'add'    }, { name: 'remove', value: 'remove' },
        { name: 'play',   value: 'play'   }, { name: 'rename', value: 'rename' },
      ))
    .addStringOption(o => o.setName('name').setDescription('Playlist name'))
    .addIntegerOption(o => o.setName('position').setDescription('Song position (for remove)').setMinValue(1))
    .addStringOption(o => o.setName('newname').setDescription('New name (for rename)')),

  // Liked
  new SlashCommandBuilder().setName('like').setDescription('Like the current song'),
  new SlashCommandBuilder().setName('unlike').setDescription('Unlike the current song'),
  new SlashCommandBuilder().setName('liked').setDescription('View/play liked songs')
    .addStringOption(o => o.setName('action').setDescription('play to queue all').setChoices({ name: 'play', value: 'play' })),

  // Premium
  new SlashCommandBuilder().setName('vote').setDescription('Vote for Zero on Top.gg for 12hr premium'),
  new SlashCommandBuilder().setName('premium').setDescription('Check premium status'),
  new SlashCommandBuilder().setName('filter').setDescription('Apply audio filter (Premium)')
    .addStringOption(o => o.setName('name').setDescription('Filter name').setRequired(true)
      .setChoices(
        { name: 'Bass Boost',  value: 'bass'       },
        { name: '8D Audio',    value: '8d'         },
        { name: 'Nightcore',   value: 'nightcore'  },
        { name: 'Vaporwave',   value: 'vaporwave'  },
        { name: 'Tremolo',     value: 'tremolo'    },
        { name: 'Vibrato',     value: 'vibrato'    },
        { name: 'Normalizer',  value: 'normalizer' },
        { name: 'Reset',       value: 'reset'      },
      )),
  new SlashCommandBuilder().setName('247').setDescription('Toggle 24/7 mode (Premium)'),
  new SlashCommandBuilder().setName('djrole').setDescription('Set/clear DJ role (Premium)')
    .addRoleOption(o => o.setName('role').setDescription('Role to set as DJ (omit to clear)')),
].map(c => c.toJSON());

const rest = new REST({ version: '10' }).setToken(process.env.DISCORD_TOKEN);

(async () => {
  console.log('Deploying slash commands…');
  try {
    await rest.put(Routes.applicationCommands(process.env.CLIENT_ID), { body: commands });
    console.log(`✅ Deployed ${commands.length} slash commands globally.`);
  } catch (e) {
    console.error(e);
  }
})();
