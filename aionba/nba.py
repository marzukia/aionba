import pandas as pd
from collections import defaultdict

from aionba.core import construct_url, fetch_urls


async def get_players(proxies=None):
    """ Return back dataframe with a dataframe of players.
        Pass through '1' if you want only current players.
    """
    endpoint = "commonallplayers"
    params = {
        "LeagueID": "00",
        "Season": "2018-19",
        "IsOnlyCurrentSeason": "0"
    }
    url = construct_url(endpoint, params)
    if proxies:
        response = await fetch_urls(url, proxies=proxies)
    else:
        response = await fetch_urls(url)
    data = response[0]["resultSets"][0]["rowSet"]
    headers = [i.lower() for i in response[0]["resultSets"][0]["headers"]]
    df = pd.DataFrame(data, columns=headers)
    return df


async def get_common_player_info(player_ids, proxies=None):
    if type(player_ids) is not list:
        player_ids = [player_ids]
    endpoint = "commonplayerinfo"
    urls = []
    for player_id in player_ids:
        params = {
            "PlayerID": player_id,
        }
        url = construct_url(endpoint, params)
        urls.append(url)
    if proxies:
        response = await fetch_urls(urls, proxies=proxies)
    else:
        response = await fetch_urls(urls)
    player_arr = []
    for result in response:
        result = result["resultSets"][0]
        result_dict = {k: v for k, v in zip(result["headers"], result["rowSet"][0])}
        player_arr.append(result_dict)
    df = pd.DataFrame(player_arr).drop_duplicates("PERSON_ID", keep="last")
    df.columns = [i.lower() for i in df.columns]
    return df


async def get_player_career_stats(player_ids, proxies=None):
    if type(player_ids) is not list:
        player_ids = [player_ids]
    endpoint = "playercareerstats"
    urls = []
    for player_id in player_ids:
        params = {
            "PlayerID": player_id,
            "PerMode": "Totals",
        }
        url = construct_url(endpoint, params)
        urls.append(url)
    if proxies:
        response = await fetch_urls(urls, proxies=proxies)
    else:
        response = await fetch_urls(urls)
    data = defaultdict(list)
    headers = {}
    for player in response:
        for category in player['resultSets']:
            headers[category['name']] = [i.lower() for i in category['headers']]
            for row in category['rowSet']:
                if row is not []:
                    data[category['name']].append(row)
    dfs = {}
    for key, value in data.items():
        dfs[key] = pd.DataFrame(value, columns=headers[key])
    return dfs
