import csv
import glob
import json
import logging
import os.path

from common import *
from common import TempEntry


event_types = {
    1: 'MADE SHOT',
    2: 'MISSED SHOT',
    3: 'FREE THROW ATTEMPT',
    4: 'REBOUND',
    5: 'OUT OF BOUNDS, FOUL, TURNOVER',
    6: 'PERSONAL FOUL',
    7: 'SHOT CLOCK VIOLATION?',
    8: 'SUBSTITUTION',
    9: 'TIMEOUT',
    10: 'JUMP BALL',
    11: 'PLAYER EJECTION',
    12: 'PERIOD START',
    13: 'PERIOD END?',
    18: 'GAME END?'
}


'''
The ball changes possession when:
1. A team makes a shot (#1)
2. A team makes a rebound (#4) x
3. Out of bounds / turnover (#5)
4. Makes the final free throw of a series of free throws
5. Wins a jump ball
6. A player if fouled (maybe)

'''


def pretty_print_entry(entry, headers):
    print('-------------------')
    for header in sorted(headers):
        if header == 'EVENTMSGTYPE' and entry[headers[header]] in event_types:
            print('{0} = {1}'.format(header, event_types[entry[headers[header]]]))
        else:
            print('{0} = {1}'.format(header, entry[headers[header]]))


def get_headers(data):
    headers_to_index = dict(enumerate(data))
    return {v: k for k, v in list(headers_to_index.items())}


def get_home_score(entry, headers):
    return int(entry[headers['SCORE']].split(' - ')[1])


def get_visitor_score(entry, headers):
    return int(entry[headers['SCORE']].split(' - ')[0])


def seconds_elapsed(entry, headers):
    period = int(entry[headers['PERIOD']])
    assert 0 < period <= 7, 'period {0} does not appear valid'.format(period)
    minutes_left_in_period = int(entry[headers['PCTIMESTRING']].split(':')[0])
    assert 0 <= minutes_left_in_period <= 12, 'time string {0} appears invalid'.format(
        entry[headers['PCTIMESTRING']])
    seconds_left_in_minute = int(entry[headers['PCTIMESTRING']].split(':')[1])
    assert 0 <= seconds_left_in_minute < 60
    seconds_left_in_period = minutes_left_in_period * 60 + seconds_left_in_minute
    total_seconds_elapsed = ((period - 1) * 12 * 60) + (12 * 60 - seconds_left_in_period)
    return total_seconds_elapsed


def extract_temp_entry_for_free_throw(home_score, away_score, entry, headers, game):
    # pretty_print_entry(entry, headers)
    description = entry[headers['HOMEDESCRIPTION']]
    shooting_team_id = entry[headers['PLAYER1_TEAM_ID']]
    is_home = shooting_team_id == game['home_team_id']
    if description is None:
        description = entry[headers['VISITORDESCRIPTION']]
    free_throw_counts = re.compile('.*(\d) of (\d).*').findall(description)
    if len(free_throw_counts) == 0:
        last_free_throw = True
    else:
        last_free_throw = free_throw_counts[0][0] == free_throw_counts[0][1]
    if entry[headers['SCORE']] is None:
        # The player missed the free throw
        if last_free_throw:
            # Last free throw and the player missed, the ball can be rebounded
            team_with_possession = 'none'
        else:
            # Not the last free throw, shooting team retains possession
            team_with_possession = shooting_team_id
    else:
        # The player made the free throw, add an entry with the score change
        if last_free_throw:
            # If it was the last free throw and they scored, it goes to the opposing team
            if shooting_team_id == game['visitor_team_id']:
                team_with_possession = game['home_team_id']
            else:
                team_with_possession = game['visitor_team_id']
        else:
            # They made the free throw, but this isn't the last one.
            team_with_possession = shooting_team_id
        home_score = get_home_score(entry, headers)
        away_score = get_visitor_score(entry, headers)
    total_seconds_elapsed = seconds_elapsed(entry, headers)
    if is_home:
        return TempEntry(
            total_seconds_elapsed, game['home_team_id'], home_score, away_score, team_with_possession)
    else:
        return TempEntry(
            total_seconds_elapsed, game['visitor_team_id'], away_score, home_score, team_with_possession)


def extract_temp_entry_for_missed_shot(home_score, away_score, entry, headers, game):
    shooting_team_id = entry[headers['PLAYER1_TEAM_ID']]
    is_home = shooting_team_id == game['home_team_id']
    team_with_possession = 'none'
    total_seconds_elapsed = seconds_elapsed(entry, headers)
    if is_home:
        return TempEntry(
            total_seconds_elapsed, game['home_team_id'], home_score, away_score, team_with_possession)
    else:
        return TempEntry(
            total_seconds_elapsed, game['visitor_team_id'], away_score, home_score, team_with_possession)


def extract_temp_entry_for_made_shot(entry, headers, game):
    # The score seems to be of the format home - away, e.g. "4 - 11", "15 - 2", etc
    # The score margin seems to be the away value minus the home value, except when they are even, which
    # shows up as TIE
    # Player 2 appears to be the player that takes the ball from the opposing team post shot
    total_seconds_elapsed = seconds_elapsed(entry, headers)
    shooting_team_id = entry[headers['PLAYER1_TEAM_ID']]
    is_home = shooting_team_id == game['home_team_id']
    # The team id of the player which takes the ball after the shot
    team_with_possession = entry[headers['PLAYER2_TEAM_ID']]
    # The new score after the shot was made
    home_score = get_home_score(entry, headers)
    away_score = get_visitor_score(entry, headers)
    if is_home:
        return TempEntry(
            total_seconds_elapsed, game['home_team_id'], home_score, away_score, team_with_possession)
    else:
        return TempEntry(
            total_seconds_elapsed, game['visitor_team_id'], away_score, home_score, team_with_possession)


def extract_temp_entry_for_rebound(home_score, away_score, entry, headers, game):
    # The team id of the player which rebounded the ball
    total_seconds_elapsed = seconds_elapsed(entry, headers)
    rebounding_team_id = entry[headers['PLAYER1_TEAM_ID']]
    team_with_possession = rebounding_team_id
    is_home = rebounding_team_id == game['home_team_id']
    if is_home:
        return TempEntry(
            total_seconds_elapsed, game['home_team_id'], home_score, away_score, team_with_possession)
    else:
        return TempEntry(
            total_seconds_elapsed, game['visitor_team_id'], away_score, home_score, team_with_possession)


def extract_temp_entry_for_jump_ball(home_score, away_score, entry, headers, game):
    total_seconds_elapsed = seconds_elapsed(entry, headers)
    team_with_possession = entry[headers['PLAYER3_TEAM_ID']]
    is_home = team_with_possession == game['home_team_id']
    if is_home:
        return TempEntry(
            total_seconds_elapsed, game['home_team_id'], home_score, away_score, team_with_possession)
    else:
        return TempEntry(
            total_seconds_elapsed, game['visitor_team_id'], away_score, home_score, team_with_possession)


def extract_temp_entry_for_turnover(home_score, away_score, entry, headers, game):
    total_seconds_elapsed = seconds_elapsed(entry, headers)
    # Player one is the player which committed the turnover. This might be travelling, stolen ball, bad pass, whatever
    # so there might be more players involved, but all we care about is that it's a turnover.
    if entry[headers['PLAYER1_TEAM_ID']] == game['visitor_team_id']:
        team_with_possession = game['home_team_id']
    else:
        team_with_possession = game['visitor_team_id']
    is_home = team_with_possession == game['home_team_id']
    if is_home:
        return TempEntry(
            total_seconds_elapsed, game['home_team_id'], home_score, away_score, team_with_possession)
    else:
        return TempEntry(
            total_seconds_elapsed, game['visitor_team_id'], away_score, home_score, team_with_possession)


def extract_nba_pbp_entries():
    games_examined = 0
    games_skipped = 0
    games = []
    for game_file in glob.glob('data/nba_stats/*pbp*.json'):
        if 'empty_game' in game_file:
            continue
        games_examined += 1
        try:
            game_data = json.load(open(game_file))
            if len(game_data['resultSets']) != 2:
                raise RuntimeError('found data with a result set size != 2'.format(game_file))
            nba_game_id = game_data['parameters']['GameID']

            # load the summary information so that we know who is home and who is away
            raw_summary_data = json.load(open('data/nba_stats/{game_id}_summary.json'.format(game_id=nba_game_id)))
            summary_headers = get_headers(raw_summary_data['headers'])
            summary_data = raw_summary_data['rowSet'][0]
            # pretty_print_entry(raw_summary_data['rowSet'][0], summary_headers)

            headers = get_headers(game_data['resultSets'][0]['headers'])
            entries = game_data['resultSets'][0]['rowSet']

            game = {
                'home_team_id': summary_data[summary_headers['HOME_TEAM_ID']],
                'home_team_abbrev': 'unknown',
                'visitor_team_id': summary_data[summary_headers['VISITOR_TEAM_ID']],
                'visitor_team_abbrev': 'unknown',
                'winner': 'unknown',
                'nba_game_id': nba_game_id,
                'game_date': summary_data[summary_headers['GAME_DATE_EST']].split('T')[0]
            }
            in_game_entries = []
            team_id_to_abbrev = {}
            home_score = 0
            away_score = 0

            for entry in entries:
                # pretty_print_entry(entry, headers)
                team_id_to_abbrev[entry[headers['PLAYER1_TEAM_ID']]] = entry[headers['PLAYER1_TEAM_ABBREVIATION']]
                if entry[headers['SCORE']] is not None:
                    home_score = get_home_score(entry, headers)
                    away_score = get_visitor_score(entry, headers)
                event_type = int(entry[headers['EVENTMSGTYPE']])
                new_temp_entry = None
                if event_type == 1:
                    # Player made the shot
                    new_temp_entry = extract_temp_entry_for_made_shot(entry, headers, game)
                elif event_type == 2:
                    # Missed shot
                    new_temp_entry = extract_temp_entry_for_missed_shot(home_score, away_score, entry, headers, game)
                elif event_type == 3:
                    # Free throw attempt
                    new_temp_entry = extract_temp_entry_for_free_throw(home_score, away_score, entry, headers, game)
                elif event_type == 4:
                    # Rebound
                    new_temp_entry = extract_temp_entry_for_rebound(home_score, away_score, entry, headers, game)
                elif event_type == 5:
                    # Out of bounds, turnover, steal
                    new_temp_entry = extract_temp_entry_for_turnover(home_score, away_score, entry, headers, game)
                elif event_type == 6:
                    # Personal Foul
                    continue
                elif event_type == 7:
                    # Violation?
                    continue
                elif event_type == 8:
                    # Substitution
                    continue 
                elif event_type == 9:
                    # Timeout
                    continue 
                elif event_type == 10:
                    # jump ball
                    new_temp_entry = extract_temp_entry_for_jump_ball(home_score, away_score, entry, headers, game)
                elif event_type == 11:
                    # Player ejected
                    continue 
                elif event_type == 12:
                    # Period start
                    continue 
                elif event_type == 13:
                    # End of a period
                    continue # Don't record anything
                elif event_type == 18:
                    # Unclear, maybe game end?
                    continue 
                else:
                    pretty_print_entry(entry, headers)
                    raise RuntimeError('unknown event type {0}'.format(event_type))
                if new_temp_entry is not None:
                    in_game_entries.append(new_temp_entry)
                    # print(new_temp_entry)
            if home_score > away_score:
                game['winner'] = game['home_team_id']
            else:
                game['winner'] = game['visitor_team_id']
            winning_score = home_score
            losing_score = away_score
            if game['winner'] == game['visitor_team_id']:
                winning_score = away_score
                losing_score = home_score
            print('{0} won {1} by a score of {2} to {3}'.format(
                team_id_to_abbrev[game['winner']], summary_data[summary_headers['GAMECODE']],
                winning_score, losing_score))
            game['entries'] = in_game_entries
            game['visitor_team_abbrev'] = team_id_to_abbrev[game['visitor_team_id']]
            game['home_team_abbrev'] = team_id_to_abbrev[game['home_team_id']]
            games.append(game)
        except RuntimeError as e:
            logging.warning('skipping {0} because {1}'.format(game_file, e))
            games_skipped += 1
        # if games_examined > 100:
        #     break
        break
    if games_skipped > 0:
        logging.warning('Skipped {0} of {1} games because of errors'.format(games_skipped, games_examined))
    return games


def make_buckets(games, time_bin_size):
    # map of bucket_key to [number of times won, total number of games]
    buckets = {}

    for game in games:
        for entry in game['entries']:
            # The "direct bucket" is the bucket reflecting the situation caused by the team in the entry.
            # For instance if the Warriors are up by three points against the Cavaliers with 100 seconds into the game
            # and win, this is the bucket produced by that situation. The opposite is also true, that if you were down
            # by three points 100 seconds into the game, it resulted in a loss.
            direct_bucket_key = make_bucket_key(
                entry.total_seconds_elapsed, entry.team_score - entry.opp_score, time_bin_size)
            direct_bucket = [0, 0]
            if direct_bucket_key in buckets:
                direct_bucket = buckets[direct_bucket_key]
            if game['winner'] == entry.team:
                direct_bucket[0] += 1
            direct_bucket[1] += 1
            buckets[direct_bucket_key] = direct_bucket

            opposite_bucket_key = make_bucket_key(
                entry.total_seconds_elapsed, entry.opp_score - entry.team_score, time_bin_size)
            opposite_bucket = [0, 0]
            if opposite_bucket_key in buckets:
                opposite_bucket = buckets[opposite_bucket_key]
            if game['winner'] != entry.team:
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
    games = extract_nba_pbp_entries()
    buckets = make_buckets(games, time_bin_size)
    write_bball_data(buckets, time_bin_size)

if __name__ == "__main__":
    make_buckets_file(time_bin_size=10)
