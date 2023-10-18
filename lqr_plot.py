import numpy as np
import matplotlib.pyplot as plt

## Color Palette
# https://matplotlib.org/stable/gallery/color/named_colors.html
# https://matplotlib.org/stable/tutorials/colors/colors.html
# https://matplotlib.org/stable/tutorials/colors/colormaps.html
# https://matplotlib.org/stable/tutorials/colors/colorbar_only.html
# darkorange, deepskyblue

def cdf_plot(ax, vals, label = "test", color = "deepskyblue"):
    vals = np.sort(np.array(vals))
    y_vals = np.arange( len(vals) ) / float(len(vals) - 1)
    ax.grid(True, alpha = 0.5)
    return ax.plot(vals, y_vals, label = label , color = color)

def pmf_plot(ax, vals, labels = "test", bins = 100, color = "deepskyblue", **kwargs):
    if "normalized" in kwargs:
        if kwargs["normalized"]:
            lns = ax.hist(vals, density = True, histtype='step', bins=bins, label = labels , color = color)
            step = bins[1] - bins[0]
            locs = ax.get_yticks()
            ax.set_yticks(locs, np.round(locs * step, 5))
            return lns
    return ax.hist(vals, density = True, histtype='step', bins=bins, label = labels , color = color)

def twin_ax_legend(ax, **kwargs):
    lns = []
    for key,value in kwargs.items():
        if key == "hist":
            for _value in value:
                lns += _value[-1]
        elif key == "plot":
            for _value in value:
                lns += _value
    labs = [l.get_label() for l in lns]
    ax.legend(lns, labs)
    return ax

def line_plot(ax, x_vals, y_vals, style = '-*', label = "None"):
    ax.style.use("grayscale")
    ax.grid(True, alpha = 0.5)
    return ax.plot(x_vals, y_vals, style, label = label)