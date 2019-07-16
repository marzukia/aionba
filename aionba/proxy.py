import asyncio
import aiohttp

import re
import ssl
import contextlib
from lxml import html


async def fetch_proxies():
    """ Fetch new proxy from:
        https://api.getproxylist.com/proxy
    """
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "accept_encdoing": "gzip, deflate, br",
        "user_agent": "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:67.0) Gecko/20100101 Firefox/67.0"
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        response = await session.get("https://free-proxy-list.net/")
        response = await response.text()
        tree = html.fromstring(response)
        proxies = []
        for row in tree.xpath("//table[1]/tbody[1]/tr"):
            regex = "<[^>]*>|'|b"
            ip = html.tostring(row.xpath('td[1]')[0])
            port = html.tostring(row.xpath('td[2]')[0])
            proxy = re.sub(regex, '', f"{ip}:{port}")
            proxies.append(proxy)
        return proxies


async def ping_proxy(proxy):
    """ Function to ping the proxy and return ms in an integer. """
    proxy = proxy.split(":")[0]
    regex = r"(time=\d+.ms+)"
    cmd = f"ping -c 1 {proxy}"
    ping = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await ping.communicate()
    assert stdout is not None, "Ping command failed."
    try:
        ping = re.search(regex, str(stdout)).group(1)
        ping = int(ping.split('=')[-1][:-3])
        return ping
    except AttributeError:
        return 999


@contextlib.contextmanager
def suppress_ssl_exception_report():
    """ Despite exception being handled, asyncio event loop prints traceback.
        Function mutes it for duration of proxy check.
        Exceptions are expected during this process.
        https://stackoverflow.com/questions/52012488/ssl-asyncio-traceback-even-when-error-is-handled
    """
    loop = asyncio.get_event_loop()
    old_handler = loop.get_exception_handler()

    def old_handler_fn(loop, ctx):
        loop.default_exception_handler(ctx)

    def ignore_exc(_loop, ctx):
        exc = ctx.get('exception')
        if isinstance(exc, ssl.SSLError):
            return
        old_handler_fn(loop, ctx)

    loop.set_exception_handler(ignore_exc)
    try:
        yield
    finally:
        loop.set_exception_handler(old_handler)


async def test_proxy(proxy, session, threshold):
    """ Check if proxy is connectable.
    """
    proxy = 'http://' + proxy
    timeout = aiohttp.ClientTimeout(total=threshold)
    try:
        with suppress_ssl_exception_report():
            response = await session.get('http://yahoo.com', proxy=proxy, timeout=timeout)
    except (
        asyncio.TimeoutError,
        aiohttp.ClientProxyConnectionError,
        aiohttp.ClientHttpProxyError,
        aiohttp.ServerDisconnectedError,
        aiohttp.ClientOSError,
        aiohttp.ClientResponseError
    ):
        return None
    return response


async def decide_proxy(proxy, session, threshold, arr):
    ping_result = await ping_proxy(proxy)
    if int(ping_result) < 500:
        test_result = await test_proxy(proxy, session, threshold)
        if test_result:
            arr.append(proxy)


async def check_proxies(proxies, threshold):
    """ Clean proxy list, checks and removes slow/invalid proxies.
    """
    async with aiohttp.ClientSession() as session:
        arr = []
        await asyncio.gather(*[decide_proxy(i, session, threshold, arr) for i in proxies])
        return arr


async def get_clean_proxies(threshold):
    assert (type(threshold) is int) or (type(threshold is float)), f"Invalid threshold type {type(threshold)}"
    proxies = await fetch_proxies()
    assert type(proxies) is list, "A list of proxies was not returned."
    clean_proxies = await check_proxies(proxies, threshold)
    assert len(clean_proxies) > 0, "List of clean proxies was less than one."
    return clean_proxies


def fetch_proxy(proxies, i):
    """ Fetch a random proxy """
    return "http://" + proxies[i]
