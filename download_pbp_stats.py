import json
import os
import requests

base_pbp_url = 'http://stats.nba.com/stats/playbyplayv2?StartPeriod=0&EndPeriod=0&tabView=playbyplay&GameID={game_id}'
base_summary_url = 'http://stats.nba.com/stats/boxscoresummaryv2?GameID={game_id}'


def make_all_game_ids():
    game_ids = []
    for year in range(2, 15):
        for season_code in [2, 4]:
            # 001: Pre Season
            # 002: Regular Season
            # 003: All - Star
            # 004: Post Season
            max_game_number = 1231
            if season_code == 4:
                max_game_number = 400
            for game_number in range(1, max_game_number):
                game_id = '{season_code:0>3}{season_year:0>2}{game_number:0>5}'\
                    .format(season_code=season_code, season_year=year, game_number=game_number)
                game_ids.append(game_id)
    return game_ids


empty_game_string = ''
with open(os.getcwd() + '/data/nba_stats/000_empty_game.json', 'r') as f:
    empty_game_string = json.dumps(json.load(f))


for game_id in make_all_game_ids():
    pbp_file_name = os.getcwd() + '/data/nba_stats/{game_id}_pbp.json'.format(game_id=game_id)
    summary_file_name = os.getcwd() + '/data/nba_stats/{game_id}_summary.json'.format(game_id=game_id)
    if os.path.isfile(pbp_file_name) and os.path.isfile(summary_file_name):
        print('already have')
        continue
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'}
    r = requests.get(base_pbp_url.format(game_id=game_id), headers=headers)
    print(base_pbp_url.format(game_id=game_id))
    if r.status_code != 200:
        continue
    if len(r.json()['resultSets'][0]['rowSet']) == 0:
        continue
    with open(pbp_file_name, 'w') as outfile:
        json.dump(r.json(), outfile)
    r = requests.get(base_summary_url.format(game_id=game_id), headers=headers)
    with open(summary_file_name, 'w') as outfile:
        json.dump(r.json()['resultSets'][0], outfile)
