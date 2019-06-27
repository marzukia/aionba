# aionba
Asynchronous NBA.com/stats API wrapper, utilising `asyncio`, `aiohttp`, and `aiosqlite` libraries for the backend. 
Caching functionality built into request calls to reduce overhead on API, proxy and header rotation to avoid bans.
This library aims to allow the user to consistently update their NBA stats database.

## Usage
### Proxy
`aionba` builds in a proxy list builder, this allows you to *hopefully* avoid being detected and blocked.
In order to fetch a list of proxies, use `await aionba.proxy.fetch_proxies()`, then use `await aionba.proxy.check_proxies()` on the results.

### Core
This part is still a WIP.
