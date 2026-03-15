import { Player } from "discord-player";
import { YoutubeiExtractor, SpotifyExtractor } from "@discord-player/extractor";

export async function createPlayer(client) {
  const player = new Player(client, {
    ytdlOptions: {
      quality: "highestaudio",
      highWaterMark: 1 << 25
    }
  });

  await player.extractors.loadDefault((ext) => ext !== "YouTubeExtractor");

  await player.extractors.register(YoutubeiExtractor, {});
  await player.extractors.register(SpotifyExtractor, {});

  player.events.on("playerStart", (queue, track) => {
    queue.metadata?.channel?.send({
      content: `🎵 Now playing: **${track.title}** \`[${track.duration}]\``
    }).catch(() => {});
  });

  player.events.on("connectionError", (queue, error) => {
    queue.metadata?.channel?.send("⚠️ There was a connection error in the voice channel.").catch(() => {});
    console.error("Connection error:", error);
  });

  player.events.on("error", (queue, error) => {
    queue.metadata?.channel?.send("⚠️ An error occurred while playing music.").catch(() => {});
    console.error("Player error:", error);
  });

  player.events.on("emptyChannel", (queue) => {
    // Intentionally keep 24/7 support; do not destroy automatically
    // You can add an idle timeout here if you ever want it.
  });

  return player;
}

