import csv
import matplotlib.pyplot as plt
import numpy as np

# Read in the data from the CSV file
with open('./log/N1N2_latency.csv', 'r') as f:
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

plt.savefig('./fig/N1N2_5G.pdf')
