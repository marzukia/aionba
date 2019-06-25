import aiohttp
import aiosqlite

import json
from datetime import datetime

from .settings import *
from .proxy import *


async def check_existing_query(db, url):
    """ Checks local SQLite3 DB to see if requested URL is stored.
        If a table isn't found, one is created.
        TODO: Add a timer setting when re-cache needs to occur.
    """
    sql = f"SELECT * FROM query_cache WHERE query = '{url}'"
    try:
        cursor = await db.execute(sql)
    except aiosqlite.OperationalError:
        await db.execute("CREATE TABLE query_cache(query VARCHAR, date DATETIME, response VARCHAR);")
        return None
    return await cursor.fetchone()


async def store_response(db, url, response):
    """ Store response in SQLite3 DB. """
    payload = {
        "query": url,
        "date": datetime.now(),
        "response": response
    }
    payload = ",".join(f"'{i}'" for i in payload.values())
    sql = f"INSERT INTO query_cache(query, date, response) VALUES({payload})"
    await db.execute(sql)
    await db.commit()


async def fetch_url(url, proxies):
    """ Check if URL is cached first via check_existing_query(),
        If none is found, fetch then store response.
        Otherwise, return cached response.
    """
    async with aiosqlite.connect(SQLITE_PATH) as db:
        query = await check_existing_query(db, url)
        if not query:
            async with aiohttp.ClientSession() as session:
                proxy = "http://" + fetch_proxy(proxies)
                response = await session.get(url, proxy=proxy)
                response = await response.json()
                await store_response(db, url, json.dumps(response))
                return response
        else:
            return json.loads(query[-1])


def construct_url(endpoint):
    """ Construct URL based on endpoint name.
        https://github.com/seemethere/nba_py/wiki/stats.nba.com-Endpoint-Documentation
        Documentation states https://stat.nba.com/stats/<endpoint>/?<params>
    """
    return f"https://stats.nba.com/stats/{endpoint}"
