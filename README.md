# aionba
Asynchronous NBA.com/stats API wrapper, utilising `asyncio`, `aiohttp`, and `aiosqlite` libraries for the backend. 
Caching functionality built into request calls to reduce overhead on API, proxy and header rotation to avoid bans.
This library aims to allow the user to consistently update their NBA stats database.

## Usage
### Proxy
`aionba` builds in a proxy list builder, this allows you to *hopefully* avoid being detected and blocked.
In order to fetch a list of proxies, use `await aionba.proxy.get_clean_proxies(threshold=3)`.

### Core
The key function which this wrapper uses is `await aionba.core.fetch_urls([a, b, c], proxies=proxy_arr)` which will asynchronously retrieve those values.

Once a url is retrieved, it'll be cached in a sqlite database. It will only re-retrieve the url if the cached query is older than `aionba.settings.MAX_CACHE_AGE`.
