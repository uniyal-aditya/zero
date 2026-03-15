/**
 * Unified context object so every command works for both
 * prefix messages and slash interactions without duplication.
 */
function ctx(msgOrInt, isSlash) {
  if (isSlash) {
    return {
      isSlash: true,
      raw: msgOrInt,
      guild: msgOrInt.guild,
      guildId: msgOrInt.guildId,
      channel: msgOrInt.channel,
      member: msgOrInt.member,
      user: msgOrInt.user,
      author: msgOrInt.user,
      reply: d => msgOrInt.replied || msgOrInt.deferred
        ? msgOrInt.followUp(d)
        : msgOrInt.reply(d),
      defer: () => msgOrInt.deferReply(),
      editReply: d => msgOrInt.editReply(d),
    };
  }
  return {
    isSlash: false,
    raw: msgOrInt,
    guild: msgOrInt.guild,
    guildId: msgOrInt.guild.id,
    channel: msgOrInt.channel,
    member: msgOrInt.member,
    user: msgOrInt.author,
    author: msgOrInt.author,
    reply: d => msgOrInt.reply(d),
    defer: () => Promise.resolve(),
    editReply: d => msgOrInt.reply(d),
  };
}

module.exports = { ctx };
