import matplotlib.pyplot as plt
import json
import numpy as np

def get_data():
    """
    Get a list of all embed times for all runs
    :return: List of values
    """

    with open('test_results.json', 'r') as f:
        data = json.load(f)

    value_list = []

    for key, values in data.items():
        for item in values:
            for key_s, value_s in item.items():
                value_list.append(value_s / 1e3)

    return value_list


def simple_plot(data):
    plot_data = data['0']

    plt_x = []
    plt_y = []

    for item in plot_data:
        for key, value in item.items():
            plt_x.append(int(key))
            plt_y.append(value / 1e3)

    plt.plot(plt_x, plt_y)
    plt.ylabel('Time in µs')
    plt.show()

def load_mult_topo_data():
    with open('results_20_topos.json', 'r') as f:
        data = json.load(f)

    value_dict = {}

    for topo_name, values in data.items():
        value_dict[topo_name] = []
        for run_nr, item_list in values.items():
            for item in item_list:
                for key_s, value_s in item.items():
                    value_dict[topo_name].append(value_s / 1e3)

    return value_dict


def ecdf_values(x):
    """
    Generate values for empirical cumulative distribution function

    Params
    --------
        x (array or list of numeric values): distribution for ECDF

    Returns
    --------
        x (array): x values
        y (array): percentile values
    """

    # Sort values and find length
    x = np.sort(x)
    n = len(x)
    # Create percentiles
    y = np.arange(1, n + 1, 1) / n
    return x, y


def ecdf_plot(x, name='Value', log_scale=False, save=False, save_name='Default'):
    if type(x) == dict:
        fig = plt.figure(figsize=(10, 6))
        ax = plt.subplot(1, 1, 1)
        for key, value in x.items():
            xs, ys = ecdf_values(value)

            plt.step(xs, ys, linewidth=2.5, c='b')
    else:
        xs, ys = ecdf_values(x)
        fig = plt.figure(figsize=(10, 6))
        ax = plt.subplot(1, 1, 1)
        plt.step(xs, ys, linewidth=2.5, c='b')

    if log_scale:
        ax.set_xscale('log')

    # Add ticks
    plt.xticks(size=16)
    plt.yticks(size=16)
    # Add Labels
    plt.xlabel(f'{name}', size=18)
    plt.ylabel('Percentile', size=18)

    # fit the labels into the figure
    plt.title(f'ECDF of {name}', size=20)
    plt.tight_layout()
    plt.show()

    if save:
        plt.savefig(save_name + '.png')

if __name__ == '__main__':
    data = load_mult_topo_data()
    ecdf_plot(data, name='Embed Time in µs')
