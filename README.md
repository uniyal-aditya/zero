# 🎵 Zero Music Bot

> A feature-rich, high-definition Discord music bot — *Made by Aditya</>*

---

## ✨ Features

- 🎵 **HD Audio** from YouTube & Spotify (tracks, albums, playlists)
- ▶️ Full player controls — play, pause, resume, skip, back, forward, rewind, seek
- 🔀 Shuffle • 🔁 Loop (track / queue) • ♾️ Autoplay
- 📋 Queue management — view, remove, move, clear, skip-to
- 📁 Personal playlists — create, edit, play
- ❤️ Liked Songs — like/unlike, play all
- ⭐ Premium system — server-level (owner-granted) + 12-hour vote premium (Top.gg)
- 🎛️ Audio filters — Bass Boost, 8D, Nightcore, Vaporwave, and more (Premium)
- 🔒 24/7 Mode — bot stays in VC (Premium)
- 🎧 DJ Role — restrict controls to a role (Premium)
- 📖 Interactive dropdown help menu
- 💬 @mention → sends bot about message with footer **Made by Aditya</>**

---

## 🚀 Setup

### 1. Prerequisites

- Node.js **v18.x** (v18.20.x works fine) or **v20+**
  > ⚠️ **Node 18 users:** The bot includes an automatic `File` polyfill — the `ReferenceError: File is not defined` crash is already fixed. No action needed.
- FFmpeg installed and in your PATH
  - Windows: https://ffmpeg.org/download.html
  - Linux: `sudo apt install ffmpeg`
  - macOS: `brew install ffmpeg`

### 2. Clone & Install

```bash
git clone <your-repo>
cd ZeroBot
npm install
```

### 3. Configure

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable               | Where to get it |
|------------------------|-----------------|
| `DISCORD_TOKEN`        | [Discord Developer Portal](https://discord.com/developers/applications) → Bot → Token |
| `SPOTIFY_CLIENT_ID`    | [Spotify Dashboard](https://developer.spotify.com/dashboard) |
| `SPOTIFY_CLIENT_SECRET`| Same as above |
| `TOPGG_TOKEN`          | [Top.gg API](https://top.gg/api/docs) |
| `TOPGG_BOT_ID`         | Your bot's ID on Top.gg |

Also set `CLIENT_ID` in `.env` for slash command deployment:
```
CLIENT_ID=your_bot_application_id
```

### 4. Discord Bot Settings

In the Developer Portal:
- **Privileged Gateway Intents:** Enable `Message Content Intent`, `Server Members Intent`
- **OAuth2 Scopes:** `bot`, `applications.commands`
- **Bot Permissions:** `Connect`, `Speak`, `Send Messages`, `Embed Links`, `Read Message History`, `Use External Emojis`, `Add Reactions`

### 5. Deploy Slash Commands

```bash
npm run deploy
```

### 6. Start the Bot

```bash
npm start
# or for development with auto-restart:
npm run dev
```

---

## 📋 Commands

### 🎵 Music  (prefix `-` or `/`)

| Command | Aliases | Description |
|---------|---------|-------------|
| `-play <query/URL>` | `-p` | Play from YouTube or Spotify |
| `-pause` | | Pause playback |
| `-resume` | | Resume playback |
| `-skip` | `-s` | Skip current track |
| `-back` | `-b`, `-prev` | Previous track |
| `-stop` | | Stop & clear queue |
| `-nowplaying` | `-np` | Current track info |
| `-forward [s]` | `-ff` | Fast-forward N seconds |
| `-rewind [s]` | `-rw` | Rewind N seconds |
| `-seek <mm:ss>` | | Seek to timestamp |
| `-volume <1-200>` | `-v` | Set volume |
| `-lyrics [song]` | | Get lyrics |
| `-leave` | `-dc` | Disconnect bot |

### 📋 Queue

| Command | Description |
|---------|-------------|
| `-queue [page]` / `-q` | View queue |
| `-shuffle` | Shuffle queue |
| `-loop` | Cycle loop modes |
| `-autoplay` | Toggle autoplay |
| `-skipto <pos>` | Jump to position |
| `-remove <pos>` | Remove a track |
| `-move <from> <to>` | Reorder track |
| `-clear` | Clear queue |

### 📁 Playlists

| Command | Description |
|---------|-------------|
| `-pl create <name>` | Create a playlist |
| `-pl delete <name>` | Delete a playlist |
| `-pl list` | All your playlists |
| `-pl view <name>` | View songs in playlist |
| `-pl add <name>` | Add current song |
| `-pl remove <name> <pos>` | Remove song from playlist |
| `-pl play <name>` | Queue entire playlist |
| `-pl rename <old> <new>` | Rename a playlist |

### ❤️ Liked Songs

| Command | Description |
|---------|-------------|
| `-like` | Like current song |
| `-unlike` | Unlike current song |
| `-liked` | View liked songs |
| `-liked play` | Queue all liked songs |

### ⭐ Premium

| Command | Description |
|---------|-------------|
| `-vote` | Vote on Top.gg for 12hr Premium |
| `-premium` | Check your premium status |
| `-filter <name>` | Apply audio filter |
| `-247` | Toggle 24/7 mode |
| `-djrole [@role]` | Set/clear DJ role |

**Available filters:** `bass` `8d` `nightcore` `vaporwave` `tremolo` `vibrato` `normalizer` `fadein` `reverse` `reset`

### 👑 Owner (Aditya only)

| Command | Description |
|---------|-------------|
| `-premium grant <guildId>` | Grant server premium |
| `-premium revoke <guildId>` | Revoke server premium |
| `-premium list` | All premium servers |
| `-premium status <guildId>` | Server premium info |
| `-setstatus <text>` | Change bot status |
| `-eval <code>` | Run JavaScript |
| `-announce <msg>` | DM all guild owners |

---

## ⭐ Premium System

### Server Premium (Permanent)
Granted by the bot owner (Aditya) via `-premium grant <guildId>`.
Unlocks all premium features for the **entire server**.

### Vote Premium (12 Hours)
Any **user** can vote for Zero on [Top.gg](https://top.gg) and run `-vote` to claim 12 hours of personal premium access.

---

## 📁 Project Structure

```
ZeroBot/
├── data/                    # JSON persistence (auto-created)
│   ├── premium.json
│   ├── votes.json
│   ├── playlists.json
│   ├── likedSongs.json
│   └── settings.json
├── src/
│   ├── commands/
│   │   ├── music/           # play, controls, queue, lyrics, help
│   │   ├── playlist/        # playlist, liked songs
│   │   ├── premium/         # filters, 24/7, djrole, vote, premium
│   │   └── owner/           # eval, setstatus, announce
│   ├── events/              # ready, messageCreate, interactionCreate, voiceStateUpdate
│   ├── utils/
│   │   ├── database.js      # JSON file-based data store
│   │   ├── embeds.js        # All embed builders + help menu
│   │   ├── permissions.js   # Owner/premium/DJ checks
│   │   ├── topgg.js         # Top.gg vote checking
│   │   └── ctx.js           # Unified prefix+slash context
│   ├── config.js
│   ├── deploy-commands.js
│   └── index.js
├── .env.example
├── package.json
└── README.md
```

---

## 🛠️ Troubleshooting

**Bot joins but no audio** → Make sure FFmpeg is installed and in PATH.

**Spotify links not working** → Double-check `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` in `.env`.

**Vote premium not granting** → Ensure `TOPGG_TOKEN` and `TOPGG_BOT_ID` are correct.

**Slash commands not showing** → Run `npm run deploy` and wait up to 1 hour for Discord to propagate.

---

*Zero Music Bot — Made by Aditya</>*
