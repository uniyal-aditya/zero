const https  = require('https');
const cfg    = require('../config');

/**
 * Returns true if the user has voted for the bot on Top.gg
 * within the last 12 hours (Top.gg resets vote status after 12hr).
 */
function hasVoted(userId) {
  return new Promise(resolve => {
    if (!cfg.topggToken || !cfg.topggBotId) return resolve(false);
    const req = https.request(
      {
        hostname: 'top.gg',
        path: `/api/bots/${cfg.topggBotId}/check?userId=${userId}`,
        headers: { Authorization: cfg.topggToken },
      },
      res => {
        let raw = '';
        res.on('data', c => (raw += c));
        res.on('end', () => {
          try { resolve(JSON.parse(raw).voted === 1); }
          catch { resolve(false); }
        });
      }
    );
    req.on('error', () => resolve(false));
    req.end();
  });
}

module.exports = { hasVoted };
