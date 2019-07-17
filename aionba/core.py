import asyncio
import aiohttp
import aiosqlite
from async_timeout import timeout

import os
import sqlite3
import json
from datetime import datetime
from urllib.parse import urlencode

from .settings import MAX_CACHE_AGE, SQLITE_PATH


async def check_existing_query(db, url):
    """ Checks local SQLite3 DB to see if requested URL is stored.
        If a table isn't found, one is created.
        If a query is found, checks max cache age in settings to see if it should be returned.
    """
    try:
        sql = f"SELECT * FROM query_cache WHERE query = '{url}'"
        cursor = await db.execute(sql)
    except Exception as e:
        print(sql)
        raise e
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


async def get_url(url, session, db, proxy=None, errors=[]):
    """ Gets URL with a random proxy if one has been passed, else None is used.
        TODO: Need to add rotating user agent probably.
    """
    response = None
    query = await check_existing_query(db, url)
    headers = {
        "host": "stats.nba.com",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "connection": "keep-alive",
        "user-agent": "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:67.0) Gecko/20100101 Firefox/67.0",
    }
    if not query:
        try:
            async with timeout(5):
                proxy_str = None
                if proxy:
                    proxy_str = "http://" + proxy
                response = await session.get(url, proxy=proxy_str, headers=headers)
                status = response.status
                print(status, url)
                response = await response.json()
                await store_response(db, url, json.dumps(response))
                if status != 200 or response == []:
                    print("ERROR:", status, url)
                    errors.append((url, proxy))
                elif status == 200 and response != []:
                    return response
        except (asyncio.TimeoutError, TimeoutError):
            pass
    else:
        return json.loads(query[-1])


def pop_urls(urls, n):
    if n > len(urls):
        n = len(urls)
    return [urls.pop() for _ in range(0, n)]


async def proxy_check_gather(session, db, errors, urls, proxies=None):
    if proxies:
        response = await asyncio.gather(*[get_url(url=j, session=session, db=db, proxy=proxies[i], errors=errors) for i, j in enumerate(urls)])
    else:
        response = await asyncio.gather(*[get_url(url=i, session=session, db=db, proxy=None, errors=errors) for i in urls])
    return response


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
    async with aiosqlite.connect(SQLITE_PATH) as db:
        async with aiohttp.ClientSession() as session:
            assert type(urls) is list, "Input urls are not a list"
            while len(urls) > 0:
                errors = []
                if not proxies:
                    # Default chnk size set if no proxies are passed through.
                    # TODO: Need to confirm optimal size here to avoid throttling.
                    chunk_size = 10
                else:
                    chunk_size = len(proxies)
                urls_chunk = pop_urls(urls, chunk_size)
                response = await proxy_check_gather(session=session, db=db, errors=errors, urls=urls_chunk, proxies=proxies)
                responses += response
                if len(errors) > 0:
                    print(errors)
                    print(f"{len(errors)} occured, retrying those urls...")
                    print("Sleeping for 5 seconds before retrying.")
                    await asyncio.sleep(5)
                    error_urls = []
                    for url, proxy in errors:
                        if proxies:
                            proxies.remove(proxy)
                        error_urls.append(url)
                    responses += await fetch_urls(urls=error_urls, proxies=proxies)
                responses = [i for i in responses if i is not None]
                print(f"{len(response)} of {len(urls_chunk)} urls processed, sleeping for 5 seconds.")
                await asyncio.sleep(5)
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
