import re

score_extract = re.compile('([A-Z]{3}) (\d+)-(\d+)')
teams_extract = re.compile('\d{8}([A-Z]{3})([A-Z]{3})')

def to_nearest_bin(number, bin_size):
    if number % bin_size > bin_size / 2:
        return number + (bin_size - number % bin_size)
    return number - number % bin_size


def timestr_to_seconds(timestr):
    parts = timestr.split(':')
    minutes = int(parts[1])
    seconds = int(parts[2])
    total_seconds = minutes * 60 + seconds
    if parts[0].startswith('-'):
        return -1 * total_seconds
    return total_seconds


def seconds_to_timestr(total_seconds):
    new_minutes = abs(total_seconds // 60)
    new_seconds = abs(total_seconds % 60)
    prefix = '+'
    if total_seconds < 0:
        prefix = '-'
    return "{0}00:{1:0=2d}:{2:0=2d}".format(prefix, new_minutes, new_seconds)


def round_to_second(total_seconds_elapsed, bin_size):
    return to_nearest_bin(total_seconds_elapsed, bin_size)


def point_diff_percentage(score, other_score, bin_size):
    diff = float(score - other_score)
    percentage = round(to_nearest_bin(diff / float(score + other_score), bin_size), 2)
    if percentage == -0.0:
        return str(0.0)
    return str(percentage)


def make_bucket_key(total_seconds_elapsed, abs_score_diff, time_bin_size):
    return str(round_to_second(total_seconds_elapsed, time_bin_size)) + ',' + str(abs_score_diff)


class TempEntry:
    'Contains the time, team, team score, and opponent score but does not know the outcome of the game.'

    def __init__(self, total_seconds_elapsed, team, is_home, team_score, opp_score):
        self.total_seconds_elapsed = total_seconds_elapsed
        self.team = team
        self.is_home = is_home
        self.team_score = team_score
        self.opp_score = opp_score


class Entry:
    'Contains the time, score, opponent_score, if they were the home team, and whether or not the team won the game.'

    def __init__(self, total_seconds_elapsed, is_home, score, opp_score, won, game_id):
        self.total_seconds_elapsed = total_seconds_elapsed
        self.is_home = is_home
        self.score = int(score)
        self.opp_score = int(opp_score)
        self.won = won
        self.game_id = game_id

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '[total_seconds_elapsed = {0}, home = {1}, score = {2}, opp_score = {3}, won_game = {4}, game_id = {5}]'\
            .format(self.total_seconds_elapsed, self.is_home, self.score, self.opp_score, self.won, self.game_id)