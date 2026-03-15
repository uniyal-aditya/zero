const cfg = require('../config');
const db  = require('./database');

const isOwner     = id  => id === cfg.ownerId;
const inVC        = m   => !!m?.voice?.channelId;
const hasPremium  = (gId, uId) => db.hasAccess(gId, uId);

function sameVC(member, player) {
  const queue = player.nodes.get(member.guild.id);
  if (!queue) return true;
  return member.voice.channelId === queue.channel?.id;
}

function isDJ(member, guildId) {
  if (!member) return false;
  if (isOwner(member.id)) return true;
  if (member.permissions.has('ManageGuild')) return true;
  const { djRole } = db.getSettings(guildId);
  if (djRole) return member.roles.cache.has(djRole);
  return true; // no DJ role = everyone can control
}

module.exports = { isOwner, inVC, sameVC, isDJ, hasPremium };
