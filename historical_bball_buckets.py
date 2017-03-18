import json
import logging
import os.path

from process_pbp_stats import extract_nba_pbp_entries


def to_nearest_bin(number, bin_size):
    if number % bin_size > bin_size / 2:
        return number + (bin_size - number % bin_size)
    return number - number % bin_size


def round_to_second(total_seconds_elapsed, bin_size):
    return to_nearest_bin(total_seconds_elapsed, bin_size)


def make_bucket_key(total_seconds_elapsed, abs_score_diff, time_bin_size):
    return str(round_to_second(total_seconds_elapsed, time_bin_size)) + ',' + str(abs_score_diff)


def get_historical_win_percentage(historical_data, time_remaining, home_score, away_score):
    bucket_key = make_bucket_key(time_remaining,
                                 home_score - away_score,
                                 historical_data['time_bin_size'])
    buckets = historical_data['buckets']
    if bucket_key not in buckets:
        raise RuntimeError
    wins = buckets[bucket_key][0]
    total_games = buckets[bucket_key][1]
    win_percent = wins / float(total_games)
    logging.debug('for a score of {0} to {1} at {5}, the number of times they have won is {2} out of {3} times, {4}%.' \
                  .format(home_score, away_score, wins, total_games, win_percent,
                          round_to_second(time_remaining, historical_data['time_bin_size'])))
    return win_percent


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
    f = 'data/cache/basketball_buckets_{0}.json'.format(time_bin_size)
    if not os.path.isfile(f):
        logging.warning('The file {0} does not exist, creating new buckets'.format(f))
        make_buckets_file(time_bin_size=time_bin_size)
        logging.warning('Buckets file creation completed!')
    with open(f, 'r') as f:
        return json.load(f)


def make_buckets_file(time_bin_size):
    games = extract_nba_pbp_entries()
    buckets = make_buckets(games, time_bin_size)
    write_bball_data(buckets, time_bin_size)

if __name__ == "__main__":
    make_buckets_file(time_bin_size=10)

