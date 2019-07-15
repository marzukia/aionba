import asyncio
import aiohttp
import aiosqlite

import os
import sqlite3
import json
from datetime import datetime
from urllib.parse import urlencode

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
            return query
        else:
            return None
    else:
        return None


async def store_response(db, url, response):
    """ Store response in SQLite3 DB. """
    payload = {
        "query": url,
        "date": datetime.now(),
        "response": response.replace("'", "''")
    }
    sql = f"INSERT INTO query_cache(query, date, response) VALUES('{payload['query']}', '{payload['date']}', '{payload['response']}')"
    await db.execute(sql)
    await db.commit()


async def get_url(url, session, arr, db, proxy=None):
    """ Gets URL with a random proxy if one has been passed, else None is used.
        TODO: Need to add rotating user agent probably.
    """
    query = await check_existing_query(db, url)
    headers = {
        "host": "stats.nba.com",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "connection": "keep-alive",
        "user-agent": "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:67.0) Gecko/20100101 Firefox/67.0",
    }
    if not query:
        response = await session.get(url, proxy=proxy, headers=headers)
        response = await response.json()
        await store_response(db, url, json.dumps(response))
        await asyncio.sleep(2)
        return response
    else:
        return json.loads(query[-1])


async def fetch_urls(urls, proxies=None, len_arr=1, responses=[]):
    """ Check if URL is cached first via check_existing_query(),
        If none is found, fetch then store response.ipyt
        Otherwise, return cached response.
    """
    if type(urls) is not list:
        urls = [urls]
    if not os.path.isfile(SQLITE_PATH):
        """ Check if SQLite3 database exists already.
            If not, create one and create the relevant table.
        """
        cur = sqlite3.connect(SQLITE_PATH).cursor()
        cur.execute("CREATE TABLE query_cache(query VARCHAR, date DATETIME, response VARCHAR);")
    chunk_size = 10
    if len(urls) > chunk_size:
        chunks = [urls[i:i + chunk_size] for i in range(0, len(urls), chunk_size)]
    else:
        chunks = [urls]
    async with aiosqlite.connect(SQLITE_PATH) as db:
        async with aiohttp.ClientSession() as session:
            assert type(urls) is list, "Input urls are not a list"
            proxy = None
            arr = []
            for chunk in chunks:
                print(len(chunk))
                if proxy:
                    response = await asyncio.gather(*[get_url(i, session, arr, db, proxy=fetch_proxy(proxies)) for i in chunk])
                else:
                    response = await asyncio.gather(*[get_url(i, session, arr, db) for i in chunk])
                print(response)
                responses += response
                print(responses)
                await asyncio.sleep(3)
        return responses


def construct_url(endpoint, params=None):
    """ Construct URL based on endpoint name.
        https://github.com/seemethere/nba_py/wiki/stats.nba.com-Endpoint-Documentation
        Documentation states https://stat.nba.com/stats/<endpoint>/?<params>
    """
    if params:
        params = urlencode(params)
    url = f"https://stats.nba.com/stats/{endpoint}?{params}"
    return url


'''
urls = [...]
tasks = set()
while urls:
     url = urls.pop()
     if len(tasks) > 10:
         finished, tasks = await asyncio.wait(tasks,
             return_when=asyncio.FIRST_COMPLETED)
     task = asyncio.create_task(session.get(url))
     tasks.add(task)
await asyncio.wait(tasks) #remaining
'''
