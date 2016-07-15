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

    def __init__(self, total_seconds_elapsed, team, team_score, opp_score, team_with_possession):
        self.total_seconds_elapsed = total_seconds_elapsed
        self.team = team
        self.team_score = team_score
        self.opp_score = opp_score
        self.team_with_possession = team_with_possession

    def __str__(self):
        return '{0} seconds; {1} team; {2} score; {3} opponent score; {4} has possession;'\
            .format(self.total_seconds_elapsed,
                    self.team,
                    self.team_score,
                    self.opp_score,
                    self.team_with_possession)
