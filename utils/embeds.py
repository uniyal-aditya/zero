import discord
import time
import config as cfg


FOOTER = "Zero Music • Made by Aditya</>"


def _footer():
    return {"text": FOOTER}


# ── HELPERS ───────────────────────────────────────────────────────────────────

def progress_bar(player: "wavelink.Player") -> str:
    if not player.current:
        return ""
    pos   = player.position          # ms
    total = player.current.length    # ms
    if not total:
        return ""
    pct   = min(pos / total, 1.0)
    fill  = round(pct * 20)
    bar   = "█" * fill + "░" * (20 - fill)
    cur   = _ms_to_str(pos)
    tot   = _ms_to_str(total)
    return f"`{cur}` {bar} `{tot}`"


def _ms_to_str(ms: int) -> str:
    s = ms // 1000
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def loop_label(mode) -> str:
    import wavelink
    return {
        wavelink.QueueMode.normal:   "Off",
        wavelink.QueueMode.loop:     "🔂 Track",
        wavelink.QueueMode.loop_all: "🔁 Queue",
    }.get(mode, "Off")


# ── NOW PLAYING ───────────────────────────────────────────────────────────────

def now_playing(player) -> discord.Embed:
    t = player.current
    queue_size = len(player.queue)
    e = discord.Embed(
        title=t.title,
        url=t.uri,
        colour=cfg.COL_PRIMARY
    )
    e.set_author(name="♪  Now Playing")
    if t.artwork:
        e.set_thumbnail(url=t.artwork)
    e.add_field(name="👤 Artist",    value=t.author or "Unknown",          inline=True)
    e.add_field(name="⏱ Duration",  value=_ms_to_str(t.length),           inline=True)
    e.add_field(name="🔊 Volume",   value=f"{player.volume}%",             inline=True)
    e.add_field(name="🔄 Loop",     value=loop_label(player.queue.mode),   inline=True)
    e.add_field(name="📃 Queue",    value=f"{queue_size} tracks",          inline=True)
    e.add_field(name="🎵 Autoplay", value="✅" if getattr(player, "autoplay_on", False) else "❌", inline=True)
    bar = progress_bar(player)
    if bar:
        e.add_field(name="\u200b", value=bar, inline=False)
    e.set_footer(text=FOOTER)
    return e


# ── ADDED TO QUEUE ────────────────────────────────────────────────────────────

def added_to_queue(track, position: int) -> discord.Embed:
    e = discord.Embed(
        title=track.title,
        url=track.uri,
        colour=cfg.COL_SUCCESS
    )
    e.set_author(name="✅  Added to Queue")
    if track.artwork:
        e.set_thumbnail(url=track.artwork)
    e.add_field(name="👤 Artist",   value=track.author or "Unknown", inline=True)
    e.add_field(name="⏱ Duration", value=_ms_to_str(track.length),  inline=True)
    e.add_field(name="# Position", value=f"#{position}",             inline=True)
    return e


# ── QUEUE ─────────────────────────────────────────────────────────────────────

def queue_embed(player, page: int = 1) -> discord.Embed:
    import wavelink
    tracks    = list(player.queue)
    per_page  = 10
    pages     = max(1, -(-len(tracks) // per_page))   # ceiling div
    page      = max(1, min(page, pages))
    start     = (page - 1) * per_page
    slice_    = tracks[start:start + per_page]

    lines = "\n".join(
        f"`{start + i + 1}.` [{t.title}]({t.uri}) — `{_ms_to_str(t.length)}`"
        for i, t in enumerate(slice_)
    ) or "Queue is empty."

    now = player.current
    now_str = f"[{now.title}]({now.uri}) — `{_ms_to_str(now.length)}`" if now else "Nothing"

    e = discord.Embed(title="📋  Music Queue", description=lines, colour=cfg.COL_PRIMARY)
    e.add_field(name="♪ Now Playing", value=now_str, inline=False)
    e.set_footer(text=f"Page {page}/{pages} • {len(tracks)} tracks • Made by Aditya</>")
    return e


# ── SIMPLE EMBEDS ─────────────────────────────────────────────────────────────

def err(msg: str) -> discord.Embed:
    return discord.Embed(description=f"❌  {msg}", colour=cfg.COL_ERROR)


def ok(msg: str) -> discord.Embed:
    return discord.Embed(description=f"✅  {msg}", colour=cfg.COL_SUCCESS)


def info(title: str, desc: str) -> discord.Embed:
    e = discord.Embed(title=title, description=desc, colour=cfg.COL_PRIMARY)
    e.set_footer(text=FOOTER)
    return e


def premium_wall() -> discord.Embed:
    e = discord.Embed(
        title="⭐  Zero Premium Required",
        description=(
            "**This feature requires Zero Premium.**\n\n"
            f"> 🗳️ **Vote on Top.gg** for **12 hours** of free premium!\n"
            f"> [Click here to vote →]({cfg.VOTE_URL})\n\n"
            "> 👑 **Server Premium** — contact the bot owner."
        ),
        colour=cfg.COL_PREMIUM,
    )
    e.set_footer(text=FOOTER)
    return e


# ── ABOUT (fires on @mention) ─────────────────────────────────────────────────

def about(bot: discord.Client, mentioner_name: str) -> discord.Embed:
    e = discord.Embed(
        title="🎵  Zero Music Bot",
        description=(
            f"Hey **{mentioner_name}**! 👋\n\n"
            "I'm **Zero**, a high-definition music bot with everything you need.\n\n"
            "**📌 Quick Start**\n"
            "`-play <song / URL>` — Play any song\n"
            "`-help` — Full interactive command menu\n\n"
            "**🔗 Supports:** YouTube • Spotify (tracks, albums, playlists)\n"
            f"**🎛️ Prefix:** `-`  •  **Slash commands:** `/play`, `/help`…"
        ),
        colour=cfg.COL_PRIMARY,
    )
    e.add_field(name="📊 Stats",   value=f"**{len(bot.guilds)}** servers\n**{round(bot.latency*1000)}ms** ping", inline=True)
    e.add_field(name="⭐ Premium", value=f"[Vote on Top.gg]({cfg.VOTE_URL}) for 12hr free!", inline=True)
    e.add_field(name="🛠 Version", value=cfg.BOT_VERSION, inline=True)
    if bot.user and bot.user.avatar:
        e.set_thumbnail(url=bot.user.avatar.url)
    e.set_footer(text=FOOTER)
    return e


# ── HELP EMBEDS ───────────────────────────────────────────────────────────────

def help_main(bot: discord.Client) -> tuple[discord.Embed, discord.ui.View]:
    e = discord.Embed(
        title="🎵  Zero Music — Help",
        description=(
            "**Select a category below** to view its commands.\n\n"
            "> 🌐 **General** — ping, stats, serverinfo, userinfo, invite\n"
            "> 🎵 **Music** — Playback, seek, volume, lyrics\n"
            "> 📋 **Queue** — View, manage, shuffle, loop\n"
            "> 📁 **Playlists** — Create & manage personal playlists\n"
            "> ❤️ **Liked Songs** — Your personal favorites\n"
            "> ⭐ **Premium** — Filters, 24/7, DJ role & more\n"
            "> 👑 **Owner** — Bot management (restricted)\n\n"
            f"**Prefix:** `-`  •  **Slash:** `/`  •  **Support:** {cfg.SUPPORT_URL}"
        ),
        colour=cfg.COL_PRIMARY,
    )
    if bot.user and bot.user.avatar:
        e.set_thumbnail(url=bot.user.avatar.url)
    e.set_footer(text=FOOTER)
    return e, HelpView()


HELP_PAGES = {
    "general": {
        "title": "🌐  General Commands",
        "colour": cfg.COL_PRIMARY,
        "fields": [
            ("🏓 Ping",        "`-ping` — Bot latency & uptime"),
            ("📊 Stats",       "`-stats` `-botstats` — Full bot statistics"),
            ("🎵 Bot Info",    "`-botinfo` `-bot` `-info`"),
            ("🏠 Server Info", "`-serverinfo` `-si`"),
            ("👤 User Info",   "`-userinfo [@user]` `-ui` `-whois`"),
            ("🖼️ Avatar",      "`-avatar [@user]` `-av` `-pfp`"),
            ("🖼️ Banner",      "`-banner [@user]`"),
            ("🎭 Role Info",   "`-roleinfo <@role>` `-ri`"),
            ("➕ Invite",      "`-invite` `-inv` — Get bot invite link"),
            ("💬 Support",     "`-support` — Join the support server"),
        ],
    },
    "music": {
        "title": "🎵  Music Commands",
        "colour": cfg.COL_PRIMARY,
        "fields": [
            ("▶️ Play",        "`-play <query/URL>` `-p` — Play from YouTube or Spotify"),
            ("⏸ Pause",       "`-pause`"),
            ("▶️ Resume",      "`-resume`"),
            ("⏭ Skip",        "`-skip` `-s`"),
            ("⏮ Back",        "`-back` `-b` `-prev`"),
            ("⏩ Forward",     "`-forward [secs]` — Fast-forward (default 10s)"),
            ("⏪ Rewind",      "`-rewind [secs]` — Rewind (default 10s)"),
            ("🎯 Seek",        "`-seek <mm:ss>` — Jump to timestamp"),
            ("⏹ Stop",        "`-stop` — Stop & clear queue"),
            ("🔊 Volume",      "`-volume <1–200>` `-v`"),
            ("🎵 Now Playing", "`-nowplaying` `-np`"),
            ("🎤 Lyrics",      "`-lyrics [song]`"),
            ("👋 Leave",       "`-leave` `-dc`"),
        ],
    },
    "queue": {
        "title": "📋  Queue Commands",
        "colour": cfg.COL_PRIMARY,
        "fields": [
            ("📋 View",     "`-queue [page]` `-q`"),
            ("🔀 Shuffle",  "`-shuffle`"),
            ("🔁 Loop",     "`-loop` — Off → Track → Queue"),
            ("♾️ Autoplay", "`-autoplay` `-ap`"),
            ("⏭ Skip To",  "`-skipto <pos>`"),
            ("🗑 Remove",   "`-remove <pos>` `-rm`"),
            ("↕️ Move",     "`-move <from> <to>`"),
            ("🧹 Clear",    "`-clear`"),
        ],
    },
    "playlist": {
        "title": "📁  Playlist Commands",
        "colour": cfg.COL_SUCCESS,
        "fields": [
            ("📁 Create",      "`-pl create <name>`"),
            ("🗑 Delete",      "`-pl delete <name>`"),
            ("📋 List",        "`-pl list`"),
            ("👁 View",        "`-pl view <name>`"),
            ("➕ Add Song",    "`-pl add <name>` — Adds current song"),
            ("➖ Remove Song", "`-pl remove <name> <pos>`"),
            ("▶️ Play",        "`-pl play <name>` — Queue entire playlist"),
            ("✏️ Rename",      "`-pl rename <old> <new>`"),
        ],
    },
    "liked": {
        "title": "❤️  Liked Songs",
        "colour": cfg.COL_ERROR,
        "fields": [
            ("❤️ Like",     "`-like` — Like the current song"),
            ("💔 Unlike",   "`-unlike`"),
            ("📋 View",     "`-liked`"),
            ("▶️ Play All", "`-liked play` — Queue all liked songs"),
        ],
    },
    "premium": {
        "title": "⭐  Premium Commands",
        "colour": cfg.COL_PREMIUM,
        "fields": [
            ("🎛️ Filters",    "`-filter <name>` — Apply audio filter\n`bass` `8d` `nightcore` `vaporwave` `tremolo` `vibrato` `normalizer` `reset`"),
            ("🔒 24/7 Mode", "`-247` — Bot stays in VC permanently"),
            ("🎧 DJ Role",   "`-djrole [@role]` — Set/clear DJ role"),
            ("📊 Status",    "`-premium` — Check your premium status"),
            ("🗳️ Vote",      "`-vote` — Vote on Top.gg for 12hr premium"),
            ("ℹ️ How to get", "> **Server Premium** → contact bot owner\n> **12hr Premium** → vote on Top.gg"),
        ],
    },
    "owner": {
        "title": "👑  Owner Commands",
        "colour": cfg.COL_WARNING,
        "fields": [
            ("⭐ Grant",  "`-premium grant <guild_id>`"),
            ("❌ Revoke", "`-premium revoke <guild_id>`"),
            ("📋 List",   "`-premium list`"),
            ("📊 Status", "`-premium status <guild_id>`"),
            ("📢 Status", "`-setstatus <text>`"),
            ("💻 Eval",   "`-eval <code>`"),
        ],
    },
}


def help_category(cat: str) -> discord.Embed | None:
    page = HELP_PAGES.get(cat)
    if not page:
        return None
    e = discord.Embed(title=page["title"], colour=page["colour"])
    for name, value in page["fields"]:
        e.add_field(name=name, value=value, inline=False)
    e.set_footer(text=f"{FOOTER}  •  Use the menu to switch categories")
    return e


# ── HELP VIEW (dropdown + back button) ───────────────────────────────────────

class HelpSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🌐 General",      value="general",  description="ping, stats, serverinfo, userinfo, invite"),
            discord.SelectOption(label="🎵 Music",        value="music",    description="Play, pause, skip, seek, volume, lyrics"),
            discord.SelectOption(label="📋 Queue",        value="queue",    description="View queue, shuffle, loop, remove, move"),
            discord.SelectOption(label="📁 Playlists",    value="playlist", description="Create, delete, play personal playlists"),
            discord.SelectOption(label="❤️ Liked Songs",  value="liked",    description="Like songs, view & play liked songs"),
            discord.SelectOption(label="⭐ Premium",      value="premium",  description="Filters, 24/7 mode, DJ role & more"),
            discord.SelectOption(label="👑 Owner",        value="owner",    description="Owner-only bot management"),
        ]
        super().__init__(placeholder="📂  Choose a category…", options=options)

    async def callback(self, interaction: discord.Interaction):
        embed = help_category(self.values[0])
        view  = BackView()
        await interaction.response.edit_message(embed=embed, view=view)


class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(HelpSelect())


class BackButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="← Back to Menu", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        embed, view = help_main(interaction.client)
        await interaction.response.edit_message(embed=embed, view=view)


class BackView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(BackButton())
