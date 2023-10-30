import csv
import matplotlib.pyplot as plt
import numpy as np
from lqr_plot import *

S2MS = lambda x: np.array(x) * 1000

def plot_scatter():
    # Read in the data from the CSV file
    folderInd = 2
    with open(f'./log/{folderInd}/N1N2_latency.csv', 'r') as f:
        reader = csv.reader(f)
        data = list(reader)

    # take header as labels
    labels = data[0]
    # N1,N2,latency5G,latency2.4G
    # 37,39,0.0061553555240084455,0.005686533315512315
    ## read value from data
    dataDict = {}
    for label in labels:
        dataDict[label] = []
    ## take even row as label, odd data
    for i in range(1, len(data)):
        if i % 2 == 1:
            for j in range(len(labels)):
                if labels[j] == 'latency':
                    dataDict[labels[j]].append(float(data[i][j]) * 1000)
                else:
                    dataDict[labels[j]].append(float(data[i][j]))

    ## compute latency with minimum of 5G and 2.4G
    # dataDict['latency'] = []
    # for i in range(len(dataDict['latency5G'])):
    #     dataDict['latency'].append(max(dataDict['latency5G'][i], dataDict['latency2.4G'][i]))

    # scatter the data with N1 and N2 with latency as intensity
    fig, ax = plt.subplots()
    ax.scatter(dataDict['N1'], dataDict['N2'], c=dataDict['latency'], cmap='viridis')

    # set a title and labels
    ax.set_title('Latency of N1 and N2')
    ax.set_xlabel('N1')
    ax.set_ylabel('N2')
    # draw intensity bar in right
    sm = plt.cm.ScalarMappable(cmap='viridis')
    sm.set_array(dataDict['latency'])
    fig.colorbar(sm)
    # highlight the minimum latency
    minLatency = min(dataDict['latency'])
    minIndex = dataDict['latency'].index(minLatency)
    ax.scatter(dataDict['N1'][minIndex], dataDict['N2'][minIndex], c='red', s=100)
    ax.text(dataDict['N1'][minIndex] , dataDict['N2'][minIndex] + 0.3, '({}, {})'.format(dataDict['N1'][minIndex], dataDict['N2'][minIndex]), fontsize=12)

    plt.savefig(f'./fig/{folderInd}/N1N2_5G.pdf')

def plotComparisonLatency(folder1, folder2, label1, label2, saveFolder):
    def readCSV(folder):
        ## read data from folder1
        with open(f'./log/{folder}/probN1N2.csv', 'r') as f:
            reader = csv.reader(f)
            data = list(reader)
        # take header as labels
        labels = data[0]
        # store latency
        dataDict1 = {}
        for label in labels:
            dataDict1[label] = []
        ## take even row as label, odd data
        for i in range(1, len(data)):
            for j in range(len(labels)):
                dataDict1[labels[j]].append(float(data[i][j]))
        return dataDict1
    
    dataDict1 = readCSV(folder1)
    dataDict2 = readCSV(folder2)

    # plot latency in the same page
    plt.figure()
    line_plot(plt, list(range(1, len(dataDict1['latency']) + 1)),S2MS(dataDict1['latency']), label=label1)
    line_plot(plt, list(range(1, len(dataDict2['latency']) + 1)),S2MS(dataDict2['latency']), label=label2)
    print(np.mean(S2MS(dataDict1['latency'][51:]) - S2MS(dataDict2['latency'][51:])) / np.mean(S2MS(dataDict2['latency'][51:])))
    plt.xlabel("Trials")
    plt.ylabel("Latency (ms)")
    plt.legend()
    # plt.savefig(f"./fig/{saveFolder}/latencyCompar.pdf", format = 'pdf', dpi = 300)

def plotComparisonN1N2(folder1, folder2, label1, label2, saveFolder):
    def readCSV(folder):
        ## read data from folder1
        with open(f'./log/{folder}/probN1N2.csv', 'r') as f:
            reader = csv.reader(f)
            data = list(reader)
        # take header as labels
        labels = data[0]
        # store latency
        dataDict1 = {}
        for label in labels:
            dataDict1[label] = []
        ## take even row as label, odd data
        for i in range(1, len(data)):
            for j in range(len(labels)):
                dataDict1[labels[j]].append(float(data[i][j]))
        return dataDict1
    
    dataDict1 = readCSV(folder1)
    dataDict2 = readCSV(folder2)

    # plot latency in the same page
    plt.figure()
    line_plot(plt, list(range(1, len(dataDict1['N1']) + 1)),dataDict1['N1'], label=label1 + " N1")
    line_plot(plt, list(range(1, len(dataDict1['N2']) + 1)),dataDict1['N2'], label=label1 + " N2")
    line_plot(plt, list(range(1, len(dataDict2['N1']) + 1)),dataDict2['N1'], label=label2 + " N1", style='--')
    line_plot(plt, list(range(1, len(dataDict2['N2']) + 1)),dataDict2['N2'], label=label2 + " N2", style='--')
    plt.xlabel("Trials")
    plt.ylabel("N1/N2")
    plt.legend()
    plt.savefig(f"./fig/{saveFolder}/N1N2Compa.pdf", format = 'pdf', dpi = 300)

plotComparisonLatency(8,9,"With control", "Without control", saveFolder = 8)
# plotComparisonN1N2(8,9,"With control", "Without control", saveFolder = 8)