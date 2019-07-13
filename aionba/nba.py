import pandas as pd

from aionba.core import construct_url, fetch_urls


async def get_current_players():
    endpoint = "commonallplayers"
    params = {
        "LeagueID": "00",
        "Season": "2018-19",
        "IsOnlyCurrentSeason": "1"
    }
    url = construct_url(endpoint, params)
    response = await fetch_urls(url)
    data = response[0]["resultSets"][0]["rowSet"]
    headers = response[0]["resultSets"][0]["headers"]
    df = pd.DataFrame(data, columns=headers)
    return df


async def get_common_player_info(player_ids):
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
    response = await fetch_urls(urls)
    player_arr = []
    for result in response:
        result = result["resultSets"][0]
        result_dict = {k: v for k, v in zip(result["headers"], result["rowSet"][0])}
        player_arr.append(result_dict)
    df = pd.DataFrame(player_arr)
    return df
