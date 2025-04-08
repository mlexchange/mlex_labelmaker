import asyncio

from prefect import get_client


async def _check_prefect_ready():
    async with get_client() as client:
        healthcheck_result = await client.api_healthcheck()
        if healthcheck_result is not None:
            raise Exception("Prefect API is not healthy.")


def check_prefect_ready():
    return asyncio.run(_check_prefect_ready())
