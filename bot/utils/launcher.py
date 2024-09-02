import os
import glob
import asyncio
import random
import re
from dotenv import load_dotenv

from pyrogram import Client
from better_proxy import Proxy

from bot.config import settings
from bot.utils import logger
from bot.core.claimer import run_claimer
from bot.core.registrator import register_sessions


# Load environment variables
load_dotenv()

start_text = """

+-------------------------------------+
|                                     |
|          TimeFarmCryptoBot          |
|             by cryptron             |
|                                     |
+-------------------------------------+
Select an action:

    1. Create session
    2. Run claimer
"""


def get_session_names() -> list[str]:
    session_names = glob.glob('sessions/*.session')
    session_names = [os.path.splitext(os.path.basename(file))[0] for file in session_names]
    
    return sorted(session_names, key=lambda x: int(re.findall(r'\d+', x)[0]) if re.findall(r'\d+', x) else 0)


def get_proxies() -> list[Proxy]:
    if settings.USE_PROXY_FROM_FILE:
        with open(file='bot/config/proxies.txt', encoding='utf-8-sig') as file:
            proxies = [Proxy.from_str(proxy=row.strip()).as_url for row in file]
    else:
        proxies = []

    return proxies


async def create_client(session_name: str) -> Client:
    return Client(
        name=session_name,
        api_id=settings.API_ID,
        api_hash=settings.API_HASH,
        workdir='sessions/',
        plugins=dict(root='bot/plugins')
    )


async def get_tg_clients() -> list[Client]:
    session_names = get_session_names()

    if not session_names:
        raise FileNotFoundError("Not found session files")

    if not settings.API_ID or not settings.API_HASH:
        raise ValueError("API_ID and API_HASH not found in the .env file.")

    logger.info(f"Maximum session connect delay set to {settings.max_session_connect_delay} seconds")

    clients = await asyncio.gather(*[create_client(name) for name in session_names])
    return clients


async def process() -> None:
    logger.info(f"Detected {len(get_session_names())} sessions | {len(get_proxies())} proxies")

    print(start_text)

    while True:
        action = input("> ")

        if not action.isdigit():
            logger.warning("Action must be number")
        elif action not in ['1', '2']:
            logger.warning("Action must be 1 or 2")
        else:
            action = int(action)
            break

    if action == 1:
        await register_sessions()
    elif action == 2:
        tg_clients = await get_tg_clients()
        await run_tasks(tg_clients=tg_clients)


async def delayed_run_claimer(tg_client: Client, proxy: str | None, delay: float):
    logger.info(f"{tg_client.name} | Waiting {delay:.2f} seconds before starting")
    await asyncio.sleep(delay)
    await run_claimer(tg_client=tg_client, proxy=proxy)


async def run_tasks(tg_clients: list[Client]):
    proxies = get_proxies()
    tasks = []

    max_delay = settings.max_session_connect_delay
    logger.info(f"Maximum session start delay set to {max_delay} seconds")

    for i, tg_client in enumerate(tg_clients):
        proxy = proxies[i % len(proxies)] if proxies else None
        delay = random.uniform(0, max_delay)
        logger.info(f"{tg_client.name} | Scheduled to start after {delay:.2f} seconds")
        tasks.append(asyncio.create_task(delayed_run_claimer(tg_client=tg_client, proxy=proxy, delay=delay)))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(process())
