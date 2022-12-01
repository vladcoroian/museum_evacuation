import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib import colors, colorbar
import numpy as np
from random import Random


class Plotter:

    def __init__(self):
        plt.ion()

    def draw_grid(self, gdata):
        r, c = len(gdata), len(gdata[0])

        # create discrete colormap
        cmap = colors.ListedColormap(['lightblue', 'black', 'red',
                                      'lightgreen', 'darkblue', '#520000'])
        bounds = [-.5, .5, 1.5, 2.5, 3.5, 4.5, 5.5]
        norm = colors.BoundaryNorm(bounds, cmap.N)

        plt.imshow(gdata, cmap=cmap, norm=norm)

        # draw gridlines
        plt.grid(which='major', axis='both',
                 linestyle='-', color='k', linewidth=2)
        plt.xticks(np.arange(-.5, r, 1))
        plt.yticks(np.arange(-.5, c, 1))
        plt.axis('off')

    def draw_people(self, x=[], y=[], c=[]):
        #                               alive      ded    safe    unknown
        cmap = colors.ListedColormap(
            ['blue', '#2b0000', 'darkgreen', 'yellow'])
        bounds = [-.5, .5, 1.5, 2.5, 3.5]
        norm = colors.BoundaryNorm(bounds, cmap.N)

        plt.scatter(x, y, c=c, cmap=cmap, norm=norm)

    def visualize(self, graph={(3, 4): {'F': 1}}, people=[], delay=.01):
        '''
        '''

        # an arbitrary assignment of integers for each of the attributes for our
        # colormap
        attrmap = {'N': 0, 'W': 1, 'F': 2, 'S': 3, 'B': 4}

        # detect rows and columns
        r, c = 0, 0
        for loc, attrs in graph.items():
            r = max(r, loc[0]+1)
            c = max(c, loc[1]+1)

        # start with a blank grid and fill into attributes
        gdata = np.zeros(shape=(r, c))

        for loc, attrs in graph.items():
            for att in 'SWBF':
                if att not in attrs:
                    continue
                if attrs[att]:
                    gdata[loc] = attrmap[att]
                    if att == 'W' and attrs['F']:
                        gdata[loc] = 5
                    break

        # use the accumulated data to draw the grid
        self.draw_grid(gdata)

        X, Y, C = [], [], []
        for p in people:
            row, col = p.loc
            R = Random(p.id)
            x, y = col-.5 + R.random(), row-.5 + R.random()
            if p.safe:
                c = 2
            elif not p.alive:
                c = 1
            elif p.alive:
                c = 0
            else:
                c = 3  # unknown state??

            X += [x]
            Y += [y]
            C += [c]

        self.draw_people(X, Y, C)

        # matplotlib housekeeping
        plt.draw()
        plt.pause(delay)
        plt.clf()
