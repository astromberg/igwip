import csv
import glob
import json
import os.path

from common import *
from common import TempEntry, Entry


def process_temp_entries(home, away, final_home_score, final_away_score, temp_entries, game_id):
    if int(final_home_score) > int(final_away_score):
        winner = home
    else:
        winner = away
    # print 'the winner of {3} was {0} by a score of {1} to {2}'.format(winner, final_home_score, final_away_score, game_id)
    processed_entries = []
    for temp_entry in temp_entries:
        processed_entries.append(Entry(temp_entry.time, temp_entry.is_home, temp_entry.team_score, temp_entry.opp_score,
                                       temp_entry.team == winner, game_id))
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
        game_id = ''
        # entries take the form of [time, team, team_score, opponent_score]
        temp_entries = []
        for row in tsv:
            if row[1] == '1':
                entries.extend(process_temp_entries(home, away, homescore, awayscore, temp_entries, game_id))
                # set up the next game
                teams_match = teams_extract.search(row[0])
                away = teams_match.group(1)
                home = teams_match.group(2)
                awayscore = 0
                homescore = 0
                temp_entries = []
                game_id = row[0]
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
        entries.extend(process_temp_entries(home, away, homescore, awayscore, temp_entries, game_id))
        # print 'done with {0}'.format(file)
    return entries


def pretty_print_entry(headers, entry):
    for header in sorted(headers):
        print '{0} = {1}'.format(header, entry[headers[header]])


def get_headers(data):
    headers_to_index = dict(enumerate(data))
    return {v: k for k, v in headers_to_index.items()}


def extract_nba_pbp_entries():
    games_examined = 0
    processed_entries = []
    for game_file in glob.glob('data/nba_stats/*pbp*.json'):
        print game_file
        if 'empty_game' in game_file:
            continue
        games_examined += 1
        # if games_examined < 5:
        #     continue
        game_data = json.load(open(game_file))
        if len(game_data['resultSets']) != 2:
            raise RuntimeError('found data with a result set size != 2'.format(game_file))
        nba_game_id = game_data['parameters']['GameID']

        # load the summary information so that we know who is home and who is away
        raw_summary_data = json.load(open('data/nba_stats/{game_id}_summary.json'.format(game_id=nba_game_id)))
        summary_headers = get_headers(raw_summary_data['headers'])
        summary_data = raw_summary_data['rowSet'][0]
        # pretty_print_entry(summary_headers, raw_summary_data['rowSet'][0])

        headers = get_headers(game_data['resultSets'][0]['headers'])
        entries = game_data['resultSets'][0]['rowSet']
        i = 0

        home_team_id = summary_data[summary_headers['HOME_TEAM_ID']]
        visitor_team_id = summary_data[summary_headers['VISITOR_TEAM_ID']]
        temp_entries = []
        team_id_to_abbrev = {}
        team_with_possession = 'none'
        winner = 'unknown'

        for entry in entries:
            print '--- entry start ---'
            period = int(entry[headers['PERIOD']])
            assert 0 < period <= 6, 'period {0} does not appear valid'.format(period)
            minutes_left_in_period = int(entry[headers['PCTIMESTRING']].split(':')[0])
            assert 0 <= minutes_left_in_period <= 12, 'time string {0} appears invalid'.format(
                entry[headers['PCTIMESTRING']])
            seconds_left_in_minute = int(entry[headers['PCTIMESTRING']].split(':')[1])
            assert 0 <= seconds_left_in_minute < 60
            seconds_left_in_period = minutes_left_in_period * 60 + seconds_left_in_minute
            total_seconds_elapsed = ((period - 1) * 12 * 60) + (12 * 60 - seconds_left_in_period)
            # print entry[headers['EVENTMSGTYPE']]
            event_type = int(entry[headers['EVENTMSGTYPE']])
            if event_type == 1:
                print 'made shot'
                # The score seems to be of the format home - away, e.g. "4 - 11", "15 - 2", etc
                # The score margin seems to be the away value minus the home value, except when they are even, which is TIE
                home_score = int(entry[headers['SCORE']].split(' - ')[0])
                away_score = int(entry[headers['SCORE']].split(' - ')[1])
                team_abbrev = entry[headers['PLAYER1_TEAM_ABBREVIATION']]
                team_id = entry[headers['PLAYER1_TEAM_ID']]
                team_id_to_abbrev[team_id] = team_abbrev
                is_home = team_id == home_team_id
                if is_home:
                    temp_entries.append(TempEntry(total_seconds_elapsed, team_abbrev, is_home, home_score, away_score))
                else:
                    temp_entries.append(TempEntry(total_seconds_elapsed, team_abbrev, is_home, away_score, home_score))
                i += 1
                # pretty_print_entry(headers, entry)
                # if i > 20:
                #     break
            elif event_type == 2:
                print 'missed shot'
            elif event_type == 3:
                print 'free throw'
            elif event_type == 4:
                print 'rebound'
            elif event_type == 5:
                print 'out of bounds, turnover, or steal'
            elif event_type == 6:
                print 'personal foul'
            elif event_type == 7:
                print 'violation?'
            elif event_type == 8:
                print 'substitution'
            elif event_type == 9:
                print 'timeout'
            elif event_type == 10:
                print 'jump ball'
            elif event_type == 11:
                print 'player ejection'
            elif event_type == 12:
                print 'period start'
            elif event_type == 13:
                pretty_print_entry(headers, entry)
                home_score = int(entry[headers['SCORE']].split(' - ')[0])
                away_score = int(entry[headers['SCORE']].split(' - ')[1])
                if home_score > away_score:
                    winner = home_team_id
                else:
                    winner = visitor_team_id
                print 'period end'
            elif event_type == 18:
                print 'unclear, maybe game end?'
            else:
                pretty_print_entry(headers, entry)
                raise RuntimeError('unknown event type {0}'.format(event_type))
        for temp_entry in temp_entries:
            processed_entries.append(
                Entry(temp_entry.total_seconds_elapsed, temp_entry.is_home, temp_entry.team_score, temp_entry.opp_score,
                      temp_entry.team == winner, nba_game_id))
    return processed_entries


def make_buckets(entries, time_bin_size):
    # map of bucket_key to [wins, losses]
    buckets = {}

    for entry in entries:
        direct_bucket_key = make_bucket_key(entry.total_seconds_elapsed, entry.score - entry.opp_score, time_bin_size)
        direct_bucket = [0, 0]
        if direct_bucket_key in buckets:
            direct_bucket = buckets[direct_bucket_key]
        if entry.won:
            direct_bucket[0] += 1
        direct_bucket[1] += 1
        buckets[direct_bucket_key] = direct_bucket

        opposite_bucket_key = make_bucket_key(entry.total_seconds_elapsed, entry.opp_score - entry.score, time_bin_size)
        opposite_bucket = [0, 0]
        if opposite_bucket_key in buckets:
            opposite_bucket = buckets[opposite_bucket_key]
        if not entry.won:
            opposite_bucket[0] += 1
        opposite_bucket[1] += 1
        buckets[opposite_bucket_key] = opposite_bucket
    return buckets


def write_bball_data(buckets, time_bin_size):
    output = {
        'time_bin_size': time_bin_size,
        'buckets': buckets
    }
    with open('basketball_buckets_{0}.json'.format(time_bin_size), 'w') as outfile:
        json.dump(output, outfile, indent=2, sort_keys=True)


def load_or_make_historical_bball_buckets(time_bin_size=10):
    f = 'basketball_buckets_{0}.json'.format(time_bin_size)
    if not os.path.isfile(f):
        make_buckets_file(time_bin_size=time_bin_size)
    with open(f, 'r') as f:
        return json.load(f)


def make_buckets_file(time_bin_size):
    # entries = extract_bbvalue_entries()
    entries = extract_nba_pbp_entries()
    buckets = make_buckets(entries, time_bin_size)
    write_bball_data(buckets, time_bin_size)


make_buckets_file(time_bin_size=10)
