import express from "express";
import { Webhook } from "@top-gg/sdk";
import { TOPGG_WEBHOOK_AUTH, TOPGG_WEBHOOK_PORT } from "../config.js";
import { recordUserVote } from "../database/premium.js";

export function startTopggWebhook() {
  if (!TOPGG_WEBHOOK_AUTH) {
    console.warn("[top.gg] TOPGG_WEBHOOK_AUTH not set, vote premium will be disabled.");
    return;
  }

  const app = express();
  const webhook = new Webhook(TOPGG_WEBHOOK_AUTH);

  app.post("/topgg", webhook.listener((vote) => {
    const userId = vote.user;
    console.log(`[top.gg] Received vote from ${userId}`);
    recordUserVote(userId);
  }));

  app.listen(TOPGG_WEBHOOK_PORT, () => {
    console.log(`[top.gg] Webhook listening on port ${TOPGG_WEBHOOK_PORT} at path /topgg`);
    console.log("Configure this URL in your bot's top.gg page to enable 12h premium after voting.");
  });
}

