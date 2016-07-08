from common import *

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
from scipy.interpolate import griddata
import math

from historical_bball_buckets import load_or_make_historical_bball_buckets


def plot_win_probabilities(buckets, time_bin_size):
    min_time = 1000000
    max_time = -1000000
    max_score_diff = -1000000
    for key in buckets:
        timestr = key.split(',')[0]
        seconds = timestr_to_seconds(timestr)
        if seconds > max_time:
            max_time = seconds
        if seconds < min_time:
            min_time = seconds
        score_diff = int(key.split(',')[1])
        if score_diff > max_score_diff:
            max_score_diff = score_diff

    time_range = np.arange(min_time, max_time, time_bin_size)
    score_diff_range = np.arange(-1 * max_score_diff, max_score_diff, 1)
    X, Y = np.meshgrid(time_range, score_diff_range)
    bins_edges_x = []
    for score_diff in range(-1 * max_score_diff, score_diff):
        bins_edges_x.append(score_diff)
    points = []
    values = []
    for key in buckets:
        parts = key.split(',')
        time_str = parts[0]
        absolute_point_differential = float(parts[1])
        seconds = timestr_to_seconds(time_str)
        percentage_of_wins = float(buckets[key][0]) / float(buckets[key][1] + buckets[key][0])
        points.append([seconds, absolute_point_differential])
        values.append(percentage_of_wins)
        points.append([seconds, -1 * absolute_point_differential])
        values.append(1 - percentage_of_wins)

    points = np.array(points)
    values = np.array(values)
    grid_x, grid_y = np.mgrid[min_time:max_time:time_bin_size, (-1 * max_score_diff):max_score_diff:1]
    #print str(len(points) / float(len(grid_y[0]) * len(grid_y))) + '% of buckets had values'
    Z = griddata(points, values, (grid_x, grid_y), method='linear')
    #valid_count = 0
    #for row in Z:
    #    for column in row:
    #        if not math.isnan(column):
    #            valid_count += 1
    #print str(valid_count / float(len(grid_y[0]) * len(grid_y))) + '% of buckets had values after interpolation'
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.plot_surface(X.T, Y.T, Z, cmap=cm.coolwarm, linewidth=0.1, antialiased=False)
    ax.set_zlabel('% chance to win')
    ax.set_ylabel('point differential')
    ax.set_xlabel('seconds left in regulation')
    plt.show()

data = load_or_make_historical_bball_buckets()
time_bin_size = data['time_bin_size']
buckets = data['buckets']
plot_win_probabilities(buckets, time_bin_size)
