import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from matplotlib import cm
from matplotlib.colors import LightSource
from mpl_toolkits.mplot3d import axes3d

fig, [[ax1, ax2], [ax3, ax4]] = plt.subplots(nrows=2, ncols=2, subplot_kw={'projection': '3d'}, squeeze=True)

# ax1 = fig.add_subplot(211, projection='3d')
# ax2 = fig.add_subplot(212, projection='3d')
cmap = matplotlib.colormaps['Spectral']

x = []
y = []
lines = []
xi = []
yi = []
x_data = []
y_data = []
z_data = []
x_data3d = []
y_data3d = []
z_data3d = []
counter = 0
with open("datax.txt") as f, open(
        "datay.txt") as g:
    datay = g.readlines()
    datax = f.readlines()
    for line in datax:
        line = line.rstrip('\n')
        x = (line.split(","))
        x = x[0:-1]
        for i in range(len(x)):
            x[i] = float(x[i])
        xi.append(x)
    for line in datay:
        line = line.rstrip('\n')
        y = (line.split(","))
        y = y[0:-1]
        for i in range(len(y)):
            y[i] = float(y[i])
        yi.append(y)

for i in range(len(xi)):
    x = np.array(xi[i])
    y = np.array(yi[i])
    z = np.array(np.ones(180) * counter)
    # plt.plot(x, y, z)
    x_data3d.append(x)
    y_data3d.append(y)
    z_data3d.append(z)
    counter += 0.5

x_data = np.array(x_data)
y_data = np.array(y_data)
z_data = np.array(z_data)
x_data3d = np.array(x_data3d)
y_data3d = np.array(y_data3d)
z_data3d = np.array(z_data3d)

ax1.plot_surface(x_data3d, y_data3d, z_data3d, cmap='plasma')
ax2.plot_wireframe(x_data3d, y_data3d, z_data3d, color='black', linewidth=1, alpha=0.5)

ls = LightSource(270, 45)
rgb = ls.shade(z_data3d, cmap=cm.gist_earth, vert_exag=0.1, blend_mode='soft')
surf = ax3.plot_surface(x_data3d, y_data3d, z_data3d, rstride=1, cstride=1, facecolors=rgb,
                        linewidth=0, antialiased=False, shade=False)
ax3.plot_wireframe(x_data3d, y_data3d, z_data3d, color='black', linewidth=1, alpha=0.5)
ax4.scatter(x_data3d, y_data3d, z_data3d, s=0.1, color='b')
#######################################


# Customize the view angle, so it's easier to see that the scatter points lie
# on the plane y=0
ax1.view_init(elev=10., azim=-65, roll=0)
ax2.view_init(elev=10., azim=-65, roll=0)
ax3.view_init(elev=10., azim=-65, roll=0)
ax4.view_init(elev=10., azim=-65, roll=0)
plt.tight_layout()
plt.show()
