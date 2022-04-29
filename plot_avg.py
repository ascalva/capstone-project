import glob
import os
import numpy as np
import matplotlib.pyplot as plt
from collections import OrderedDict
import seaborn as sns

# sns.set()


def compute_averages(dir_pattern, file_pattern) :
    averages = {}
    stds     = {}

    for d in glob.glob(dir_pattern) :
        path_pattern = f"{d}/{file_pattern}"

        dir_properties = d.split("_")
        level   = int(dir_properties[1])
        iot_num = int(dir_properties[2])

        if level not in averages :
            averages[level] = {}
            stds[level] = {}

        running_avgs = []
        for fname in glob.glob(path_pattern) :
            with open(fname, 'r') as f :
                values = np.array(f.read().splitlines(), dtype=np.float64)
                if values.size != 0 :
                    running_avgs.append( np.average(values) )

        averages[level][iot_num] = np.average(running_avgs) * 1000.0
        stds[level][iot_num] = np.std(running_avgs) * 1000.0
    
    # averages = OrderedDict(averages)
    return averages, stds

def plot_averages(data, stds) :
    # Plot the duration times vs noise
    fig, axes = plt.subplots(figsize=(14, 7), dpi=80)
    axes.set_title("Averages of Different Service Depths", fontsize=20, pad=10)
    axes.set_ylabel("Request Roundtrip Time per Request (ms)", fontsize=14, labelpad=10)
    axes.set_xlabel("Number of Consumers", fontsize=14, labelpad=10)
    axes.set_xlim([0.7,71.0])
    axes.set_ylim([-1.0, 450.0])
    # axes.patch.set_alpha(0.9)
    fig.patch.set_alpha(0.0)

    for level, avgs in sorted(data.items()) :
        iot_nums, duration = list(zip(*sorted(avgs.items())))
        _, std_ = list(zip(*sorted(stds[level].items())))

        # axes.plot(iot_nums, duration, label=f"Service Depth: {level}", linewidth=2.5)
        axes.errorbar(iot_nums, duration, std_,  label=f"Service Depth: {level}", linewidth=2.0, capsize=3.0, elinewidth=1.5)
        # axes.plot(iot_nums, duration, ".-", label=f"Service Depth: {level}", markersize=10)


    axes.legend(fontsize=14)
    plt.savefig("averages.png", dpi=150)
    plt.show()

def main() :
    # data_<service-level>_<iot-num>
    dir_pattern = "data/data_*_*"

    # consumer_<network>_iot_<id>
    file_pattern = "consumer_?_iot_*.txt"

    data, stds = compute_averages(dir_pattern, file_pattern)
    plot_averages(data, stds)


if __name__ == "__main__" :
    main()
