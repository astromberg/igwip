import logging
import pandas as pd
import statsmodels.api as sm
from historical_bball_buckets import extract_nba_pbp_entries
from common import timestr_to_seconds

games_with_pbp = extract_nba_pbp_entries()

seconds_in_game = float(48 * 60)

data_dict = {
    'time': [],
    'away': [],
    'score_diff': [],
    'team_won': [],
    'time_score': []
}
for game in games_with_pbp:
    # print(game)
    for entry in game['entries']:
        # print(entry)
        score_diff = entry.team_score - entry.opp_score
        percentage_time_completed = entry.total_seconds_elapsed / seconds_in_game
        if percentage_time_completed < 0:
            logging.warning('{0} ignored'.format(entry))
            continue
        data_dict['time'].append(percentage_time_completed)
        data_dict['score_diff'].append(score_diff)
        if entry.team == game['home_team_id']:
            data_dict['away'].append(0)
        else:
            data_dict['away'].append(1)
        if game['winner'] == entry.team:
            data_dict['team_won'].append(1)
        else:
            data_dict['team_won'].append(0)
        data_dict['time_score'].append(score_diff * percentage_time_completed)
        logging.info(data_dict)

df = pd.DataFrame.from_dict(data_dict)

print(df)

df = df.drop(['time', 'score_diff'], 1)

print(df)
#df['intercept'] = 1.0

logit = sm.Logit(df['team_won'], df[df.columns.difference(['team_won'])])

result = logit.fit()

print(result.summary())
print(result.conf_int())
