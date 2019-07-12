import asyncio
import aiohttp
import aiosqlite

import os
import sqlite3
import json
from datetime import datetime

from .settings import MAX_CACHE_AGE, SQLITE_PATH
from .proxy import fetch_proxy


async def check_existing_query(db, url):
    """ Checks local SQLite3 DB to see if requested URL is stored.
        If a table isn't found, one is created.
        If a query is found, checks max cache age in settings to see if it should be returned.
    """
    sql = f"SELECT * FROM query_cache WHERE query = '{url}'"
    cursor = await db.execute(sql)
    query = await cursor.fetchone()
    if query:
        query_date = datetime.strptime(query[1], "%Y-%m-%d %H:%M:%S.%f")
        if ((datetime.now() - query_date).days < MAX_CACHE_AGE):
            return await query
        else:
            return None
    else:
        return None


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


async def get_url(url, session, arr, db, proxy=None):
    query = await check_existing_query(db, url)
    if not query:
        response = await session.get(url, proxy=proxy)
        response = await response.json()
        await store_response(db, url, json.dumps(response))
        return response
    else:
        return json.loads(query[-1])


async def fetch_urls(urls: [], proxies=None):
    """ Check if URL is cached first via check_existing_query(),
        If none is found, fetch then store response.ipyt
        Otherwise, return cached response.
    """
    if not os.path.isfile(SQLITE_PATH):
        """ Check if SQLite3 database exists already.
            If not, create one and create the relevant table.
        """
        cur = sqlite3.connect(SQLITE_PATH).cursor()
        cur.execute("CREATE TABLE query_cache(query VARCHAR, date DATETIME, response VARCHAR);")
    async with aiosqlite.connect(SQLITE_PATH) as db:
        async with aiohttp.ClientSession() as session:
            proxy = None
            arr = []
            if proxy:
                response = await asyncio.gather(*[get_url(i, session, arr, db, proxy=fetch_proxy(proxies)) for i in urls])
            else:
                response = await asyncio.gather(*[get_url(i, session, arr, db) for i in urls])
            return response


def construct_url(endpoint):
    """ Construct URL based on endpoint name.
        https://github.com/seemethere/nba_py/wiki/stats.nba.com-Endpoint-Documentation
        Documentation states https://stat.nba.com/stats/<endpoint>/?<params>
    """
    return f"https://stats.nba.com/stats/{endpoint}"
