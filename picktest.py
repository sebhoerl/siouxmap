import matplotlib
matplotlib.use('GTK3Cairo')

import matplotlib.pyplot as plt
import numpy as np

x = np.random.rand(100)
y = np.random.rand(100)

def onclick(event):
    print("PICK %f %f" % (event.xdata, event.ydata))

fig = plt.figure()
connection_id = fig.canvas.mpl_connect('button_press_event', onclick)

plt.scatter(x, y)
plt.show()
