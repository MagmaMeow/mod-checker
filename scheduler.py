import aioschedule
import asyncio
from bot import weekly_mod_check

async def scheduler():
    aioschedule.every().saturday.at("01:00").do(weekly_mod_check)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(60)
