import random
import string
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

from aiohttp_socks import ChainProxyConnector
from discord import WebhookAdapter
from aiohttp import ClientTimeout
from colorama import Fore
from os import path


class NitroGen:
    def __init__(self, proxies: list = None) -> None:
        colorama.init()

        self.http = aiohttp.ClientSession(
            timeout=ClientTimeout(total=60),
            connector=ChainProxyConnector.from_urls(proxies)
        )

        self.total_requests = 0
        self.failed_requests = 0
        self.successful_requests = 0

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
        resp = await self.http.get(
            "https://discordapp.com/api/v6/entitlements/gift-codes/" +
            nitro
            + "?with_application=false&with_subscription_plan=true"
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
        await self.http.close()


if __name__ == "__main__":
    proxy_path = path.join(
        path.dirname(path.realpath(__file__)),
        "socks5_proxies.txt"
    )

    if path.exists(proxy_path):
        with open(proxy_path, "r") as f_:
            proxies = f_.read().split()

        for index in range(0, len(proxies)):
            if not proxies[index].startswith("socks5://"):
                proxies[index] = "socks5://" + proxies[index]

        print(Fore.GREEN + "Proxies loaded!")
    else:
        proxies = None

        print(Fore.RED + "No proxies")

    print(Fore.WHITE)

    async def main() -> None:
        nitro_gen = NitroGen(proxies=proxies)
        scheduler = await aiojobs.create_scheduler()

        print(proxies)

        connector = ChainProxyConnector.from_urls(proxies)

        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get("http://example.com") as resp:
                print(resp.status)

        await scheduler.close()
        await nitro_gen.close()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
