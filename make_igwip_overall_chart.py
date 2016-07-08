from common import *

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
from scipy.interpolate import griddata
import math

from historical_bball_buckets import extract_bbvalue_entries

bbvalue_temp_entries = extract_bbvalue_entries()

x = []
y = []
weights = []
min_score_diff = 100000
max_score_diff = -100000
for entry in bbvalue_temp_entries:
    score_diff = entry.score - entry.opp_score
    y.append(score_diff)
    x.append(48 * 60 - timestr_to_seconds(entry.time))
    weights.append(1 / float(len(bbvalue_temp_entries)))
    if score_diff > max_score_diff:
        max_score_diff = score_diff
    if score_diff < min_score_diff:
        min_score_diff = score_diff

plt.hist2d(x, y, bins=max_score_diff - min_score_diff, weights=weights)
plt.gca().set_ylabel('point differential')
plt.gca().set_xlabel('seconds left in regulation')
plt.show()

#
# min_time = 1000000
# max_time = -1000000
# max_score_diff = -1000000
# for key in buckets:
#     timestr = key.split(',')[0]
#     seconds = timestr_to_seconds(timestr)
#     if seconds < 0:
#         continue
#     if seconds > max_time:
#         max_time = seconds
#     if seconds < min_time:
#         min_time = seconds
#     score_diff = int(key.split(',')[1])
#     if score_diff > max_score_diff:
#         max_score_diff = score_diff
#
# x_bins = np.arange(min_time, max_time + 1)
# x_vals = np.zeros(max_time - min_time + 1)
#
# y_bins = np.arange(0, max_score_diff + 1)
# y_vals = np.zeros(max_score_diff + 1)
#
# for key in buckets:
#     timestr = key.split(',')[0]
#     seconds = timestr_to_seconds(timestr)
#     if seconds < 0:
#         continue
#     score_diff = int(key.split(',')[1])
#     win_percentage = float(buckets[key][0]) / buckets[key][1]
#     weights.append(win_percentage)
#     for i in range():
#         x.append(seconds)
#         y.append(score_diff)
# plt.hist2d(x, y, bins=len(), weights=, normed=False)
# plt.gca().set_ylabel('point differential')
# plt.gca().set_xlabel('seconds left in regulation')
# plt.show()
