# aionba
Asynchronous stats.nba.com API wrapper, utilising `asyncio`, `aiohttp`, and `aiosqlite` libraries for the backend.
Caching functionality built into request calls to reduce overhead on API.
This library aims to allow the user to consistently update their NBA stats database.

Shout out to this [project](https://github.com/seemethere/nba_py/wiki/stats.nba.com-Endpoint-Documentation) for documenting the API well.

## Usage
### Core
The key function which this wrapper uses is `await aionba.core.fetch_urls([a, b, c], proxies=proxy_arr)` which will asynchronously retrieve those values.

Once a url is retrieved, it'll be cached in a sqlite database. It will only re-retrieve the url if the cached query is older than `aionba.settings.MAX_CACHE_AGE`.

### NBA
#### Get current players
Retrieves a list of current players from`commonallplayers` endpoint.

Usage: `await aionba.nba.get_current_players()` returns Pandas DataFrame.

#### Get common player info
Retrieves common player info from any player ID

Usage: `await aionba.nba.get_common_player_info([player_ids])` returns Pandas DataFrame.

##### Get player career statistics
Retrieves player career statistics, incl college etc.

Usage: `await aionba.nba.get_player_career_stats([player_ids])` returns a dictionary of Pandas DataFrames

### Proxy
__**This currently does not work as intended**__

`aionba` builds in a proxy list builder, this allows you to *hopefully* avoid being detected and blocked.
In order to fetch a list of proxies, use `await aionba.proxy.get_clean_proxies(threshold=3)`.
