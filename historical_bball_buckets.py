import csv
import glob
import json
import os.path

from common import *

class TempEntry:
    'Contains the time, team, team score, and opponent score but does not know the outcome of the game.'

    def __init__(self, time, team, is_home, team_score, opp_score):
        self.time = time
        self.team = team
        self.is_home = is_home
        self.team_score = team_score
        self.opp_score = opp_score


class Entry:
    'Contains the time, score, opponent_score, if they were the home team, and whether or not the team won the game.'

    def __init__(self, time, is_home, score, opp_score, won):
        self.time = time
        self.is_home = is_home
        self.score = int(score)
        self.opp_score = int(opp_score)
        self.won = won

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '[{0}, {1}, {2}, {3}, {4}]'.format(self.time, self.is_home, self.score, self.opp_score, self.won)


def make_bucket_key_from_entry(entry, score_bin_size, time_bin_size):
    return make_bucket_key(entry.time, entry.score, entry.opp_score, score_bin_size, time_bin_size)


def process_temp_entries(home, away, homescore, awayscore, temp_entries):
    if int(homescore) > int(awayscore):
        winner = home
    else:
        winner = away
    # print 'the winner was {0} by a score of {1} to {2}'.format(winner, homescore, awayscore)
    processed_entries = []
    for temp_entry in temp_entries:
        processed_entries.append(Entry(temp_entry.time, temp_entry.is_home, temp_entry.team_score, temp_entry.opp_score,
                                       temp_entry.team == winner))
    return processed_entries


def extract_bbvalue_entries():
    entries = []
    for f in glob.glob('data/bbvalue/*'):
        # print 'opening {0}'.format(f)
        tsv = csv.reader(open(f), delimiter='\t')
        home = ''
        away = ''
        homescore = 0
        awayscore = 0
        # entries take the form of [time, team, team_score, opponent_score]
        temp_entries = []
        for row in tsv:
            if row[1] == '1':
                entries.extend(process_temp_entries(home, away, homescore, awayscore, temp_entries))
                # set up the next game
                teams_match = teams_extract.search(row[0])
                away = teams_match.group(1)
                home = teams_match.group(2)
                awayscore = 0
                homescore = 0
                temp_entries = []
            time = row[2]
            score_match = score_extract.search(row[3])
            if not score_match:
                continue
            else:
                team = score_match.group(1)
                score = score_match.group(2)
                if team == home:
                    homescore = score
                    temp_entries.append(TempEntry(time, team, True, score, awayscore))
                else:
                    awayscore = score
                    temp_entries.append(TempEntry(time, team, False, score, homescore))
        # don't forget the last game!
        entries.extend(process_temp_entries(home, away, homescore, awayscore, temp_entries))
        # print 'done with {0}'.format(file)
    return entries


def make_buckets(entries, score_bin_size, time_bin_size):
    # map of bucket_key to [wins, losses]
    buckets = {}

    for entry in entries:
        bucket_key = make_bucket_key_from_entry(entry, score_bin_size, time_bin_size)
        if bucket_key in buckets:
            wins_losses = buckets[bucket_key]
            if entry.won:
                wins_losses[0] = wins_losses[0] + 1
            else:
                wins_losses[1] = wins_losses[1] + 1
        else:
            if entry.won:
                buckets[bucket_key] = [1, 0]
            else:
                buckets[bucket_key] = [0, 1]
    return buckets


def write_bball_data(buckets, score_bin_size, time_bin_size):
    output = {
        'score_bin_size': score_bin_size,
        'time_bin_size': time_bin_size,
        'buckets': buckets
    }
    with open('basketball_buckets_{0}_{1}.json'.format(score_bin_size, time_bin_size), 'w') as outfile:
        json.dump(output, outfile)

def read_bball_data(score_bin_size=0.03, time_bin_size=10):
    f = 'basketball_buckets_{0}_{1}.json'.format(score_bin_size, time_bin_size)
    if not os.path.isfile(f):
        make_buckets_file(score_bin_size=score_bin_size, time_bin_size=time_bin_size)
    with open(f, 'r') as f:
        return json.load(f)


def make_buckets_file(score_bin_size, time_bin_size):
    bbvalue_temp_entries = extract_bbvalue_entries()
    buckets = make_buckets(bbvalue_temp_entries, score_bin_size, time_bin_size)
    write_bball_data(buckets, score_bin_size, time_bin_size)

make_buckets_file(score_bin_size=0.03, time_bin_size=10)
