import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib import cm
import random

from make_game_charts import model_prediction

def fun(seconds, point_spread):
    return model_prediction(True, seconds, point_spread, 0, False)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
x = np.arange(0, 48 * 60, 5)
y = np.arange(-20, 20, 1)
X, Y = np.meshgrid(x, y)
zs = np.array([fun(x,y) for x,y in zip(np.ravel(X), np.ravel(Y))])
Z = zs.reshape(X.shape)

ax.plot_surface(X, Y, Z, cmap=cm.RdBu)

ax.set_xlabel('Seconds Elapsed')
ax.set_ylabel('Point Spread')
ax.set_zlabel('Win Probability')
plt.title('Win Probability Home Team')

plt.show()
