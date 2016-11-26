# Based on the discussion of win probability at PFR:
# http://www.pro-football-reference.com/about/win_prob.htm

from math import erf
from math import sqrt

def cdf(x, mean=1, stddev=1):
  x_norm = (x - mean) / stddev
  result = (1.0 + erf(x_norm / sqrt(2.0))) / 2.0
  return result

def prob(line, minutes_remaining, home_score, away_score):
  away_margin = away_score - home_score
  stddev = 13.45 / sqrt((60 / minutes_remaining))
  win_prob = 1 - cdf(away_margin + 0.5, mean=line, stddev=stddev)
  tie_prob = cdf(0.5, mean=line, stddev=stddev) - cdf(-0.5, mean=line, stddev=stddev)
  return win_prob + 0.5 * tie_prob

print prob(7.0, 60, 0, 0)

