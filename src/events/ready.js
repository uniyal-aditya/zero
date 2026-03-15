const { ActivityType } = require('discord.js');

module.exports = {
  name: 'ready',
  once: true,
  execute(client) {
    console.log(`
  ███████╗███████╗██████╗  ██████╗
  ╚══███╔╝██╔════╝██╔══██╗██╔═══██╗
    ███╔╝ █████╗  ██████╔╝██║   ██║
   ███╔╝  ██╔══╝  ██╔══██╗██║   ██║
  ███████╗███████╗██║  ██║╚██████╔╝
  ╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝
  Zero Music Bot — Made by Aditya</>
  ─────────────────────────────────────
  User : ${client.user.tag}
  Guilds: ${client.guilds.cache.size}
  ─────────────────────────────────────\n`);

    const statuses = [
      { name: '-help | Zero Music', type: ActivityType.Listening },
      { name: `${client.guilds.cache.size} servers`, type: ActivityType.Watching },
      { name: 'top.gg | vote for premium', type: ActivityType.Playing },
      { name: 'HD Music 🎵', type: ActivityType.Listening },
    ];

    let i = 0;
    const rotate = () => {
      const s = statuses[i++ % statuses.length];
      client.user.setActivity(s.name, { type: s.type });
    };
    rotate();
    setInterval(rotate, 30_000);
  },
};
