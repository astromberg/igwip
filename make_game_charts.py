import csv
import glob
import matplotlib.pyplot as plt
import datetime as dt
import logging
from matplotlib.dates import MinuteLocator
from matplotlib.ticker import MultipleLocator, FuncFormatter, Locator
from matplotlib.dates import date2num, num2date
import math

from historical_bball_buckets import load_or_make_historical_bball_buckets, extract_nba_pbp_entries, \
    get_historical_win_percentage


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
    if a == 0:
        return ''
    date = num2date(a)
    print(str(date))
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


# def logit_no_intercept(is_home, seconds_elapsed, score, opp_score):
#     percentage_time_remaining = seconds_elapsed / float(48 * 60)
#     score_diff = score - opp_score
#     away = 1
#     if is_home:
#         away = 0
#
#     # First attempt using bbvalue data
#     xb = (away * 0.3709) + (percentage_time_remaining * score_diff * 0.3237)
#
#     # Second attempt using NBA play by play data
#     # xb = (away * 0.7695) + (time_played * score_diff * 0.2956)
#     y = math.e ** xb
#     return y / (1 + y)


def model_prediction(is_home, seconds_elapsed, score, opp_score, has_possession):
    percentage_time_remaining = seconds_elapsed / float(48 * 60)
    score_diff = score - opp_score
    away = 1
    if is_home:
        away = 0
    possesses_ball = 0
    if has_possession:
        possesses_ball = 1

    # First attempt using bbvalue data
    xb = (away * -0.4483) + (percentage_time_remaining * score_diff * 0.3208) + (possesses_ball * 0.2894)

    y = math.e ** xb
    return y / (1 + y)


class GameProbabilities:
    'Contains the game id, the two team names, time samples, and a map of arrays which are win probabilities keyed by method.'

    def __init__(self, game_id, team, opposing_team, date_played, play_times, win_chances_by_method):
        self.game_id = game_id
        self.team = team
        self.opposing_team = opposing_team
        self.date_played = date_played
        self.times = play_times
        self.win_chances_by_method = win_chances_by_method


def make_win_chance_figure(team, opposing_team, win_chance_times, team_win_chances, date_played):
    plt.clf()
    for method in team_win_chances:
        plt.plot(win_chance_times, team_win_chances[method], label=method)
    plt.xlim()
    plt.gca().set_title('{0} vs {1} on {2}'.format(team, opposing_team, date_played))
    plt.gca().set_ylabel('Chance that {0} will win.'.format(team))
    plt.gcf().autofmt_xdate()
    plt.gca().xaxis.grid()
    handles, labels = plt.gca().get_legend_handles_labels()
    plt.gca().legend(handles, labels, loc=2)
    plt.gca().set_ylim([0, 1])
    # plt.gca().xaxis.set_major_locator(QuarterLocator())
    # plt.gca().xaxis.set_major_formatter(FuncFormatter(format_tick))
    # plt.savefig('data/nba_win_prob_charts/{0}_{1}_{2}.png'.format(date_played, team, opposing_team))
    plt.show()


if __name__ == '__main__':
    historical_data = load_or_make_historical_bball_buckets()
    games = extract_nba_pbp_entries()
    game_chart_data = []
    for game in games:
        game_date = dt.datetime.strptime(game['game_date'], '%Y-%m-%d')
        try:
            game_times = []
            percentages = {'historical': [], 'model': []}
            for entry in game['entries']:
                seconds_elapsed = entry.total_seconds_elapsed
                if seconds_elapsed > 12 * 4 * 60:
                    continue
                # Assume the entry is for the home team
                home_score = entry.team_score
                away_score = entry.opp_score
                if entry.team == game['visitor_team_id']:
                    # Oh no it's not for the home team, okay switch everything.
                    home_score = entry.opp_score
                    away_score = entry.team_score
                historical_win_chance = get_historical_win_percentage(historical_data,
                                                                      seconds_elapsed,
                                                                      home_score,
                                                                      away_score)
                has_possession = entry.team == entry.team_with_possession
                model_win_chance = model_prediction(
                    True, seconds_elapsed, home_score, away_score, has_possession)
                game_times.append(seconds_elapsed)
                percentages['historical'].append(historical_win_chance)
                percentages['model'].append(model_win_chance)
            game_chart_data.append(
                GameProbabilities(game['nba_game_id'],
                                  game['home_team_abbrev'],
                                  game['visitor_team_abbrev'],
                                  game['game_date'],
                                  game_times,
                                  percentages))
        except RuntimeError as e:
            logging.exception('skipping probs for {0} because of an error {1}'.format(game['nba_game_id'], e))

    for game_probabilities in game_chart_data:
        try:
            make_win_chance_figure(game_probabilities.team,
                                   game_probabilities.opposing_team,
                                   game_probabilities.times,
                                   game_probabilities.win_chances_by_method,
                                   game_probabilities.date_played)
        except ValueError as e:
            logging.exception('skipping saving {0} because of an error: {1}'
                         .format(game_probabilities.game_id, e))
