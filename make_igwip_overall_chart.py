import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D

from make_game_charts import model_prediction


def home_team(seconds, point_spread):
    return model_prediction(True, seconds, point_spread, 0, False)


def visiting_team(seconds, point_spread):
    return model_prediction(False, seconds, point_spread, 0, False)


def plot_with_function(win_prob_func, title, filename):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    x = np.arange(0, 48 * 60, 5)
    y = np.arange(-20, 20, 1)
    X, Y = np.meshgrid(x, y)
    zs = np.array([win_prob_func(x, y) for x, y in zip(np.ravel(X), np.ravel(Y))])
    Z = zs.reshape(X.shape)
    ax.set_xlabel('Seconds Elapsed')
    ax.set_ylabel('Point Spread')
    ax.set_zlabel('Win Probability')
    ax.plot_surface(X, Y, Z, cmap=cm.RdBu)
    ax.set_zticks(np.arange(0, 1 + 0.1, 0.1))
    plt.title(title)
    fig.set_size_inches(8, 5)
    fig.savefig('{0}.png'.format(filename), dpi=400)


if __name__ == '__main__':
    plot_with_function(home_team, 'Home Team', 'home_win_chances')
    plot_with_function(visiting_team, 'Visiting Team', 'visiting_win_chances')
