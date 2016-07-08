import csv
import glob
import matplotlib.pyplot as plt
import datetime as dt
from matplotlib.dates import MinuteLocator
from matplotlib.ticker import MultipleLocator, FuncFormatter, Locator
from matplotlib.dates import date2num, num2date
import math

from common import *
from historical_bball_buckets import load_or_make_historical_bball_buckets


def get_bbvalue_game_entries():
    games = []
    for f in glob.glob('data/bbvalue/*'):
        # print 'opening {0}'.format(f)
        tsv = csv.reader(open(f), delimiter='\t')
        home = ''
        away = ''
        home_score = 0
        away_score = 0
        game_id = ''
        # entries take the form of [time, team, team_score, opponent_score]
        current_game_entries = []
        for row in tsv:
            if row[1] == '1':
                if home != '':
                    games.append({
                        'game_id': game_id,
                        'home': home,
                        'away': away,
                        'scores': current_game_entries
                    })
                # set up the next game
                teams_match = teams_extract.search(row[0])
                away = teams_match.group(1)
                home = teams_match.group(2)
                away_score = 0
                home_score = 0
                current_game_entries = []
                game_id = row[0]
            time = row[2]
            score_match = score_extract.search(row[3])
            if not score_match:
                continue
            else:
                team = score_match.group(1)
                score = int(score_match.group(2))
                if team == home:
                    home_score = score
                else:
                    away_score = score
                current_game_entries.append([time, home_score, away_score])
        # don't forget the last game!
        games.append({
            'game_id': game_id,
            'home': home,
            'away': away,
            'scores': current_game_entries
        })
        # print 'done with {0}'.format(file)
    return games


class QuarterLocator(Locator):
    def tick_values(self, vmin, vmax):
        return [date2num(dt.datetime(1900, 1, 1, 0, 12, 0, 0)),
                date2num(dt.datetime(1900, 1, 1, 0, 24, 0, 0)),
                date2num(dt.datetime(1900, 1, 1, 0, 36, 0, 0)),
                vmin]

    def __call__(self, *args, **kwargs):
        vmin, vmax = self.axis.get_view_interval()
        return self.tick_values(vmin, vmax)


def format_tick(a, b):
    date = num2date(a)
    if date.minute == 12:
        return 'Q4'
    elif date.minute == 24:
        return 'Q3'
    elif date.minute == 36:
        return 'Q2'
    elif date.minute > 36:
        return 'Q1'
    else:
        return str(date.minute)


def logit_no_intercept(is_home, timestr, score, opp_score):
    time_played = 1 - (timestr_to_seconds(timestr) / float(48 * 60))
    score_diff = score - opp_score
    away = 1
    if is_home:
        away = 0
    xb = (away * -0.3079) + (time_played * score_diff * 0.3200)
    y = math.e ** xb
    return y / (1 + y)


def logit_with_intercept(is_home, timestr, score, opp_score):
    time_played = 1 - (timestr_to_seconds(timestr) / float(48 * 60))
    score_diff = score - opp_score
    away = 1
    if is_home:
        away = 0
    xb = 0.2511 + (away * -0.5571) + (time_played * score_diff * 0.3144)
    y = math.e ** xb
    return y / (1 + y)


def negative_binomial(is_home, timestr, score, opp_score):
    time_played = 1 - (timestr_to_seconds(timestr) / float(48 * 60))
    score_diff = score - opp_score
    away = 1
    if is_home:
        away = 0
    xb = (away * -0.8927) + (time_played * score_diff * 0.0483)
    y = math.e ** xb
    return y / (1 + y)

class GameProbabilities:
    'Contains the game id, the two team names, time samples, and a map of arrays which are win probabilities keyed by method.'

    def __init__(self, game_id, team, opposing_team, times, win_chances_by_method):
        self.game_id = game_id
        self.team = team
        self.opposing_team = opposing_team
        self.times = times
        self.win_changes_by_method = win_chances_by_method


def make_win_chance_figure(team, opposing_team, times, team_win_chances):
    for method in team_win_chances:
        plt.plot(times, percentages[method])
#    plt.plot(times, percentages['historical'])
    plt.gcf().autofmt_xdate()
    majorLocator = QuarterLocator()
    majorFormatter = FuncFormatter(format_tick)
    # minorLocator = MultipleLocator(5)
    plt.gca().xaxis.grid()
    plt.gca().xaxis.set_major_locator(majorLocator)
    plt.gca().xaxis.set_major_formatter(majorFormatter)
    plt.gca().invert_xaxis()

    plt.show()

    print 'blah'


# import datetime
# import random
# import matplotlib.pyplot as plt
#
# # make up some data
# x = [datetime.datetime.now() + datetime.timedelta(hours=i) for i in range(12)]
# y = [i+random.gauss(0,1) for i,_ in enumerate(x)]
#
# # plot
# plt.plot(x,y)
# # beautify the x-labels
# plt.gcf().autofmt_xdate()
#
# plt.show()
def get_historical_win_percentage(historical_data, time_remaining, home_score, away_score):
    bucket_key = make_bucket_key(time_remaining,
                                 home_score - away_score,
                                 historical_data['time_bin_size'])
    buckets = historical_data['buckets']
    print buckets[bucket_key]
    wins = buckets[bucket_key][0]
    total_games = buckets[bucket_key][1]
    win_percent = wins / float(total_games)
    print 'for a score of {0} to {1} at {5}, the number of times they have won is {2} out of {3} times, {4}%.'\
        .format(home_score, away_score, wins, total_games, win_percent, round_to_second(time_remaining, historical_data['time_bin_size']))
    return win_percent

historical_data = load_or_make_historical_bball_buckets()
games = get_bbvalue_game_entries()
game_chart_data = []
for game in games:
    times = []
    percentages = {
        'historical': [],
        'model': [],
        'model_with_intercept': [],
    }
    print game['game_id']
    for score in game['scores']:
        time_remaining = score[0]
        if (timestr_to_seconds(time_remaining)) < 0:
            continue
        parsed_time = dt.datetime.strptime(time_remaining, '%H:%M:%S')
        times.append(parsed_time)
        home_score = score[1]
        away_score = score[2]
        historical_win_chance = get_historical_win_percentage(historical_data, time_remaining, home_score, away_score)
        model_win_chance = logit_no_intercept(True, time_remaining, home_score, away_score)
        model_with_intercept_win_chance = logit_with_intercept(True, time_remaining, home_score, away_score)
        percentages['historical'].append(historical_win_chance)
        percentages['model'].append(model_win_chance)
        percentages['model_with_intercept'].append(model_with_intercept_win_chance)
    game_chart_data.append(GameProbabilities(game['game_id'], game['home'], game['away'], times, percentages))
    break

for game in game_chart_data:
    make_win_chance_figure(game.team, game.opposing_team, game.times, game.win_changes_by_method)
