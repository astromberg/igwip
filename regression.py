import pandas as pd
import statsmodels.api as sm
import pylab as pl
import numpy as np
from historical_bball_buckets import extract_bbvalue_entries
from common import timestr_to_seconds

bbvalue_temp_entries = extract_bbvalue_entries()

seconds_in_game = float(48 * 60)

data_dict = {
    'time': [],
    'away': [],
    'score_diff': [],
    'team_won': [],
    'timexscore': []
}
for entry in bbvalue_temp_entries:
    score_diff = entry.score - entry.opp_score
    percentage_time_completed = 1 - timestr_to_seconds(entry.time) / seconds_in_game
    if percentage_time_completed < 0:
        #print '{0} ignored'.format(entry.time)
        continue
    data_dict['time'].append(percentage_time_completed)
    if entry.is_home:
        data_dict['away'].append(0)
    else:
        data_dict['away'].append(1)
    data_dict['score_diff'].append(score_diff)
    if entry.won:
        data_dict['team_won'].append(1)
    else:
        data_dict['team_won'].append(0)
    data_dict['timexscore'].append(score_diff * percentage_time_completed)

df = pd.DataFrame.from_dict(data_dict)

print df

df = df.drop(['time', 'score_diff'], 1)

#df['intercept'] = 1.0

logit = sm.GLM(df['team_won'], df[df.columns.difference(['team_won'])], family=sm.families.NegativeBinomial())

result = logit.fit()

print result.summary()
print result.conf_int()
