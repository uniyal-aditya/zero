## Zero – Discord Music Bot

Zero is a high quality Discord music bot with:

- **HD audio** (highest audio quality from YouTube)
- **YouTube & Spotify** support (`/play` or `/p` and `-play` / `-p`)
- **Full music controls**: shuffle, loop, autoplay, back, forward, pause, resume, stop, queue, nowplaying
- **Playlists & liked songs** (stored in a local SQLite database)
- **24/7 mode** (no automatic disconnect)
- **Premium features**:
  - Permanent **server premium** (grantable only by the bot owner)
  - **12 hour premium** for users after they vote on top.gg

### 1. Install dependencies

```bash
cd "c:/Users/adity/Documents/DISCORD BOTS/Music_bot"
npm install
```

### 2. Configure environment

Copy `.env.example` to `.env` and fill in:

- **DISCORD_TOKEN** – your bot token
- **DISCORD_CLIENT_ID** – your bot application ID
- **DISCORD_GUILD_ID** – optional, for fast dev registration of slash commands
- **OWNER_ID** – your Discord user ID (already set to `800553680704110624`)
- **DEFAULT_PREFIX** – `-`
- **TOPGG_WEBHOOK_AUTH / TOPGG_WEBHOOK_PORT** – for the top.gg vote webhook

### 3. top.gg voting (12h premium)

1. Host the bot somewhere reachable by the internet.
2. Expose the Express server route: `POST /topgg` on `TOPGG_WEBHOOK_PORT`.
3. In your top.gg bot page, set the **Webhook URL** to your server URL and set the **Authorization** secret to `TOPGG_WEBHOOK_AUTH`.
4. When a user votes, they get **12 hours** of premium access on any server.

### 4. Running the bot

```bash
npm start
```

The bot will:

- Log in
- Register slash commands
- Start the top.gg webhook listener

