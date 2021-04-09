import random
import string
from typing import List
import aiohttp
import colorama
import aiojobs
import asyncio


try:
    import uvloop
except ImportError:
    pass
else:
    uvloop.install()

from aiohttp_socks import ProxyConnector
from discord import WebhookAdapter
from aiohttp import ClientTimeout
from colorama import Fore
from os import path


class NitroGen:
    def __init__(self) -> None:
        colorama.init()

        self.total_requests = 0
        self.failed_requests = 0
        self.successful_requests = 0

        proxy_path = path.join(
            path.dirname(path.realpath(__file__)),
            "socks5_proxies.txt"
        )

        with open(proxy_path, "r") as f_:
            proxies = f_.read().strip().split()

        self.sessions: List[aiohttp.ClientSession] = []
        for proxy in proxies:
            self.sessions.append(
                aiohttp.ClientSession(
                    connector=ProxyConnector.from_url("socks5://" + proxy),
                    timeout=ClientTimeout(total=60)
                )
            )

        self.sessions_len = len(self.sessions) - 1

        print(Fore.GREEN + "Proxies loaded!")

    async def generate_code(self, code: str = None) -> None:
        print(Fore.WHITE)

        if not code:
            code = "".join(random.choices(
                string.ascii_uppercase +
                string.digits +
                string.ascii_lowercase,
                k=16
            ))

        nitro = "https://discord.gift/" + code
        resp = await self.sessions[random.randint(0, self.sessions_len)].get(
            "https://discordapp.com/api/v6/entitlements/gift-codes/" +
            nitro
            + "?with_application=false&with_subscription_plan=true",
            verify_ssl=False
        )

        if resp.status == 200:
            self.successful_requests += 1
            print(Fore.GREEN + nitro)
        elif resp.status == 429:
            timeout = (
                resp.headers["X-RateLimit-Reset-After"]
                if "X-RateLimit-Reset-After" in resp.headers else 1.0
            )
            print(Fore.CYAN + "Timeout, retrying in " + str(timeout))
            await asyncio.sleep(timeout)
            await self.generate_code(code)
        else:
            self.failed_requests += 1
            print(Fore.RED + nitro)

        self.total_requests += 1

        print(
            "\n",
            Fore.WHITE,
            "Total: ", Fore.WHITE, self.total_requests, " | ",
            "Failed: ", Fore.RED, self.failed_requests, " | ",
            Fore.WHITE,
            "Successful: ", Fore.GREEN, self.successful_requests,
            sep=""
        )

    async def close(self) -> None:
        for session in self.sessions:
            await session.close()


if __name__ == "__main__":
    async def main() -> None:
        nitro_gen = NitroGen()
        scheduler = await aiojobs.create_scheduler()

        while True:
            await scheduler.spawn(nitro_gen.generate_code())

        await scheduler.close()
        await nitro_gen.close()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()