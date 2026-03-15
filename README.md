# 🎵 Zero Music Bot (Python)

> A feature-rich, high-definition Discord music bot — *Made by Aditya</>*

---

## ✨ Features

- 🎵 HD Audio via **Lavalink** (YouTube & Spotify)
- ▶️ Full player — play, pause, resume, skip, back, forward, rewind, seek
- 🔀 Shuffle  •  🔁 Loop (track / queue)  •  ♾️ Autoplay
- 📋 Queue — view, remove, move, clear, skip-to
- 📁 Personal playlists (create, edit, play)
- ❤️ Liked Songs — like/unlike, play all
- ⭐ Premium — server-level (owner) + 12hr vote (Top.gg)
- 🎛️ Audio Filters — Bass, 8D, Nightcore, Vaporwave, Tremolo, Vibrato (Premium)
- 🔒 24/7 Mode (Premium)
- 🎧 DJ Role (Premium)
- 📖 Interactive dropdown help menu (`-help`)
- 💬 @mention → about embed with **Made by Aditya</>** footer

---

## 🚀 Setup

### 1. Prerequisites

- Python **3.10+**
- A **Lavalink server** (handles all audio)

### 2. Setting up Lavalink

Lavalink is a separate audio server Zero connects to. You need it running.

#### Free hosting option — use lavalink.devamop.in or similar public nodes:
Edit your `.env`:
```
LAVALINK_HOST=lavalink.devamop.in
LAVALINK_PORT=443
LAVALINK_PASSWORD=DevamOP
```
> Search "free lavalink nodes 2024" for current public options.

#### Self-host (recommended):
```bash
# Requires Java 17+
wget https://github.com/lavalink-devs/Lavalink/releases/latest/download/Lavalink.jar
# Create application.yml (see below), then:
java -jar Lavalink.jar
```

Minimal `application.yml`:
```yaml
server:
  port: 2333
  address: 0.0.0.0
lavalink:
  server:
    password: "youshallnotpass"
    sources:
      youtube: true
      soundcloud: true
      http: true
plugins:
  - dependency: "dev.lavalink.youtube:youtube-plugin:1.3.0"
    repository: "https://maven.lavalink.dev/releases"
```

### 3. Install & Configure

```bash
cd ZeroBotPy
pip install -r requirements.txt

# Copy and fill in env
cp .env.example .env
# Edit .env with your values
```

| Variable               | Where to get it |
|------------------------|-----------------|
| `DISCORD_TOKEN`        | [Discord Developer Portal](https://discord.com/developers/applications) → Bot → Token |
| `LAVALINK_HOST`        | Your Lavalink server address |
| `LAVALINK_PORT`        | Lavalink port (default 2333) |
| `LAVALINK_PASSWORD`    | Lavalink password |
| `SPOTIFY_CLIENT_ID`    | [Spotify Dashboard](https://developer.spotify.com/dashboard) |
| `SPOTIFY_CLIENT_SECRET`| Same as above |
| `TOPGG_TOKEN`          | [Top.gg API](https://top.gg/api/docs) — for vote checking |
| `TOPGG_BOT_ID`         | Your bot's numeric ID on Top.gg |

### 4. Discord Bot Settings

In the Developer Portal:
- **Privileged Intents:** Enable `Message Content` and `Server Members`
- **OAuth2 Scopes:** `bot` + `applications.commands`
- **Bot Permissions:** `Connect`, `Speak`, `Send Messages`, `Embed Links`, `Use External Emojis`, `Read Message History`, `Add Reactions`

### 5. Run

```bash
python bot.py
```

Slash commands are synced automatically on startup.

---

## 📋 Commands

### 🎵 Music

| Command | Aliases | Description |
|---------|---------|-------------|
| `-play <query/URL>` | `-p` | Play from YouTube or Spotify |
| `-pause` | | Pause |
| `-resume` | | Resume |
| `-skip` | `-s` | Skip track |
| `-back` | `-b`, `-prev` | Previous track |
| `-stop` | | Stop & clear |
| `-nowplaying` | `-np` | Now playing |
| `-forward [s]` | `-ff` | Fast-forward |
| `-rewind [s]` | `-rw` | Rewind |
| `-seek <mm:ss>` | | Seek to time |
| `-volume <1-200>` | `-v` | Set volume |
| `-lyrics [song]` | | Get lyrics |
| `-leave` | `-dc` | Disconnect |
| `-help [cat]` | `-h` | Help menu |

### 📋 Queue

| Command | Description |
|---------|-------------|
| `-queue [page]` / `-q` | View queue |
| `-shuffle` | Shuffle |
| `-loop` | Cycle loop modes |
| `-autoplay` / `-ap` | Toggle autoplay |
| `-skipto <pos>` | Jump to position |
| `-remove <pos>` | Remove track |
| `-move <from> <to>` | Reorder |
| `-clear` | Clear queue |

### 📁 Playlists

| Command | Description |
|---------|-------------|
| `-pl create <n>` | Create playlist |
| `-pl delete <n>` | Delete playlist |
| `-pl list` | All your playlists |
| `-pl view <n>` | View songs |
| `-pl add <n>` | Add current song |
| `-pl remove <n> <pos>` | Remove song |
| `-pl play <n>` | Queue playlist |
| `-pl rename <old> <new>` | Rename |

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
| `-premium` | Check status |
| `-filter <n>` | Apply audio filter |
| `-247` | Toggle 24/7 mode |
| `-djrole [@role]` | Set/clear DJ role |

**Filters:** `bass` `8d` `nightcore` `vaporwave` `tremolo` `vibrato` `normalizer` `reset`

### 👑 Owner (Aditya only)

| Command | Description |
|---------|-------------|
| `-premium grant <id>` | Grant server premium |
| `-premium revoke <id>` | Revoke server premium |
| `-premium list` | All premium servers |
| `-premium status <id>` | Server info |
| `-setstatus <text>` | Change bot status |
| `-eval <code>` | Run Python |
| `-announce <msg>` | DM all guild owners |
| `-servers` | List all servers |

---

## 📁 Project Structure

```
ZeroBotPy/
├── data/               # JSON persistence (auto-created)
│   ├── premium.json
│   ├── votes.json
│   ├── playlists.json
│   ├── liked_songs.json
│   └── settings.json
├── cogs/
│   ├── music.py        # play, pause, skip, back, forward, seek, lyrics, help
│   ├── queue.py        # queue, shuffle, loop, autoplay, skipto, remove, move, clear
│   ├── playlist.py     # pl create/delete/list/view/add/remove/play/rename
│   ├── liked.py        # like, unlike, liked
│   ├── premium.py      # filter, 247, djrole, vote, premium
│   └── owner.py        # eval, setstatus, announce, servers
├── utils/
│   ├── database.py     # JSON file-based data store
│   ├── embeds.py       # All embed builders + help dropdown UI
│   ├── checks.py       # Permission decorators
│   └── topgg.py        # Top.gg vote API
├── bot.py              # Bot entry point
├── config.py           # All configuration
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⭐ Premium System

### Server Premium (Permanent)
Granted **only by Aditya** (owner ID `800553680704110624`) via:
```
-premium grant <guild_id>
```

### Vote Premium (12 Hours)
Any user votes on [Top.gg](https://top.gg) then runs `-vote` to claim 12hr personal premium.

---

*Zero Music Bot — Made by Aditya</>*
