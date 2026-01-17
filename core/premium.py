class PremiumManager:
    def __init__(self, db):
        self.db = db

    async def is_premium_user(self, user_id: int):
        return await self.db.is_premium_user(user_id)

    async def is_premium_guild(self, guild_id: int):
        return await self.db.is_premium_guild(guild_id)
