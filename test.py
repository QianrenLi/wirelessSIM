import copy
import sys
import random
import numpy as np

PREPARETX = "prepareTx"
READYTX = "readyTx"
DATA = "data"
TXTIME = "txTime"
RXTIME = "rxTime"
PAYLODALEN = "payloadLen"
CW = "cw"
CWMIN = "cwMin"
AIFS = "aifs"
TXFAILED = "txFailed" 
G5 = 0
G24 = 1
DATALEN = 68

DATAOBJ = {TXTIME: None, RXTIME: None, PAYLODALEN: 0, CWMIN : 7 , CW: 0, AIFS: 2, TXFAILED: False}
TXOBJ = {PREPARETX: None, READYTX: None, DATA:{}}
TXOBJS = {0: TXOBJ}
CHANNELOBJ = {G5: TXOBJS, G24: TXOBJS}

SLOTTIME = 20e-6
COLLISIONTIME = 0.0001


def initDataObj(id):
    _data = copy.deepcopy(DATAOBJ)
    return {id : _data}

def initTxObj():
    return copy.deepcopy(TXOBJ)

def initTxObjs(txId):
    return {txId: initTxObj()}

def initChannelObj():
    return {G5: initTxObjs(0), G24: initTxObjs(0)}

def getTxObj(txId, txObjs):
    if txId in txObjs:
        return txObjs[txId]
    else:
        txObj = copy.deepcopy(TXOBJ)
        txObjs[txId] = txObj
        return txObj
    
def sortDataObj(dataObj, key):
    def get_sort_key(item, key):
        # Replace None with a default value (e.g., empty string) for sorting
        _key = item[1][key] if item[1][key] is not None else sys.maxsize
        return _key
    assert key in [TXTIME, RXTIME]
    _dataObj = dict(sorted(dataObj.items(), key=lambda item: get_sort_key(item, key)))
    dataObj.clear()
    dataObj.update(_dataObj)
    return dataObj

    
def sortTxObjs(txObjs, key):
    def get_sort_key(item, key):
        # Replace None with a default value (e.g., empty string) for sorting

        _key = item[1][key] if item[1][key] is not None else sys.maxsize
        return _key
    assert key in [PREPARETX, READYTX]
    _txObjs = dict(sorted(txObjs.items(), key=lambda item: get_sort_key(item, key)))
    txObjs.clear()
    txObjs.update(_txObjs)
    return txObjs


def sortChannelObjs(channelObjs, key):
    def get_sort_key(item, key):
        # Replace None with a default value (e.g., empty string) for sorting
        txId = list(item[1].keys())[0]
        _key = item[1][txId][key] if item[1][txId][key] is not None else sys.maxsize
        return _key
    assert key in [PREPARETX, READYTX]
    ## sort the order of 5G and 2.4G by the tx time of the first tx packet
    sortTxObjs(channelObjs[G5], key)
    sortTxObjs(channelObjs[G24], key)
    # print(lambda item: item[1][0][key])
    _channelObjs = dict(sorted(channelObjs.items(), key=lambda item: get_sort_key(item, key)))
    channelObjs.clear()
    channelObjs.update(_channelObjs)
    return channelObjs

def addTxData(txId, txObjs, dataObj):
    txObj = getTxObj(txId, txObjs)
    _data = txObj[DATA]
    if _data is None:
        txObj[DATA] = copy.deepcopy(dataObj)
    else:
        for packetId in dataObj:
            if packetId in _data:
                _data[packetId][TXTIME] = min(dataObj[packetId][TXTIME], _data[packetId][TXTIME])
                _data[packetId][RXTIME] = max(dataObj[packetId][RXTIME], _data[packetId][RXTIME])
                _data[packetId][PAYLODALEN] += dataObj[packetId][PAYLODALEN]
            else:
                _data[packetId] = copy.deepcopy(dataObj[packetId])
    return txObj

def getTxData(txId, txObjs):
    '''
    get whole packet
    '''
    txObj = getTxObj(txId, txObjs)
    return txObj[DATA]

def getTxDataByKey(txId, txObjs, packetId):
    '''
    get packet in objs by key
    '''
    txObj = getTxObj(txId, txObjs)
    _data = txObj[DATA]
    if _data is None:
        return None
    else:
        return _data[packetId]
    
    
def updatePrepareTx(txObjs):
    for txId in txObjs:
        if sortDataObj(txObjs[txId][DATA], TXTIME) != {}:
            ## first key in data
            packetId = list(txObjs[txId][DATA].keys())[0]
            txObjs[txId][PREPARETX] = txObjs[txId][DATA][packetId][TXTIME]
        else:
            txObjs[txId][PREPARETX] = None
    return txObjs

def updateReadyTx(txObjs, CurrentTime):
    delCW = 1023
    for txId in txObjs:
        if sortDataObj(txObjs[txId][DATA], TXTIME) != {}:
            ## first key in data
            if txObjs[txId][PREPARETX] <= CurrentTime:
                packetId = list(txObjs[txId][DATA].keys())[0]
                txFailed = txObjs[txId][DATA][packetId][TXFAILED]
                cw = txObjs[txId][DATA][packetId][CW]
                cwMin = txObjs[txId][DATA][packetId][CWMIN]
                aifs = txObjs[txId][DATA][packetId][AIFS]
                if cw <= - aifs:
                    if txFailed:
                        cwMin = min(cwMin * 2, 1023)
                    cw = np.random.randint(0, cwMin)
                txObjs[txId][DATA][packetId][CW] = cw
                delCW = min(delCW, cw + aifs)
                txObjs[txId][READYTX] = txObjs[txId][DATA][packetId][TXTIME] + (cw + aifs) * SLOTTIME
            else:
                txObjs[txId][READYTX] = None
        else:
            txObjs[txId][READYTX] = None
    return delCW

def updateCW(txObjs, CurrentTime):
    for txId in txObjs:
        if sortDataObj(txObjs[txId][DATA], TXTIME) != {}:
            ## first key in data
            if txObjs[txId][PREPARETX] <= CurrentTime:
                packetId = list(txObjs[txId][DATA].keys())[0]
                delCW = np.ceil((CurrentTime - txObjs[txId][PREPARETX]) / SLOTTIME)
                txObjs[txId][DATA][packetId][CW] -= delCW
    return txObjs

def getCW(txObjs, CurrentTime):
    cws = []
    for txId in txObjs:
        if sortDataObj(txObjs[txId][DATA], TXTIME) != {}:
            ## first key in data
            if txObjs[txId][PREPARETX] <= CurrentTime:
                packetId = list(txObjs[txId][DATA].keys())[0]
                cws.append(txObjs[txId][DATA][packetId][CW])
    return cws

def getReadyTx(txObjs, CurrentTime):
    txTimes = []
    for txId in txObjs:
        if sortDataObj(txObjs[txId][DATA], TXTIME) != {}:
            ## first key in data
            if txObjs[txId][PREPARETX] <= CurrentTime:
                txTimes.append(txObjs[txId][READYTX])
    return txTimes
    
def transferTxDataByTxId(txId, txObjs, rxObjs, packetId, value, currentTime, collisionFlag = False):
    _data_slice = getTxDataByKey(txId, txObjs, packetId)
    if _data_slice is None:
        return None
    else:
        value = value if _data_slice[PAYLODALEN] > value else _data_slice[PAYLODALEN]
        histValue = _data_slice[PAYLODALEN] if collisionFlag else _data_slice[PAYLODALEN] - value
        _data_slice[PAYLODALEN] = value
        _data_slice[RXTIME] = currentTime
        addTxData(txId, rxObjs, {packetId : _data_slice})
        _data_slice[TXTIME] = currentTime
        _data_slice[PAYLODALEN] = histValue
        if histValue == 0:
            del txObjs[txId][DATA][packetId]
            return 1
    return None

def delDataById(dataObj5G, dataObj2_4G, packetId):
    if packetId in dataObj5G:
        del dataObj5G[packetId]
    if packetId in dataObj2_4G:
        del dataObj2_4G[packetId]
    return dataObj5G, dataObj2_4G
        

def generatePacketTemplate(dataObj, txTime, packetLen, packetId):
    if dataObj == {}:
        dataObj.update(initDataObj(packetId))
        dataObj[packetId][TXTIME] = txTime; dataObj[packetId][RXTIME] = None; dataObj[packetId][PAYLODALEN] = packetLen
        return
    sortDataObj(dataObj, TXTIME)
    dataObj[packetId] = {TXTIME: txTime, RXTIME: None, PAYLODALEN: packetLen}


def selectTimer(channelObj, currentTime):
    for key in channelObj:
        updatePrepareTx(channelObj[key])
    sortChannelObjs(channelObj, PREPARETX)
    ## get first PREPARETX
    key = list(channelObj.keys())[0]
    txId = list(channelObj[key].keys())[0]
    delTimer = channelObj[key][txId][PREPARETX]
    if delTimer is None:
        return currentTime
    currentTime = delTimer if delTimer > currentTime else currentTime
    ## Update READYTX
    cwMin = updateReadyTx(channelObj[key], currentTime)
    readyTxs = getReadyTx(channelObj[key], currentTime)
    updateCW(channelObj[key], currentTime)
    ## sort READYTX
    sortTxObjs(channelObj[key], READYTX)
    ## get first READYTX
    txId = list(channelObj[key].keys())[0]
    delTimer = channelObj[key][txId][READYTX]
    collisionFlag = False
    if any(np.diff(readyTxs) < COLLISIONTIME):
        collisionFlag = True
    returnTimer = delTimer if delTimer > currentTime else currentTime
    print(returnTimer, collisionFlag)
    return (returnTimer, collisionFlag)

def testGenPacket():
    channelObj = initChannelObj()
    generatePacketTemplate(channelObj[G5][0][DATA], 100, DATALEN)
    print(channelObj)
    rxChannelObj = initChannelObj()
    # print(channelObj)
    transferTxDataByTxId(0, channelObj[G5], rxChannelObj[G5], 0, 10, 10)
    print(channelObj)
    transferTxDataByTxId(0, channelObj[G5], rxChannelObj[G5], 0, 10, 20)
    print(channelObj)
    updatePrepareTx(rxChannelObj[G5])
    print(channelObj)

def dataLenToTime(dataLen , MCS):
    return dataLen * 1500 * 8 / (MCS * 1e6)

def computeDelay(dataObj):
    delay = []
    for packetId in dataObj:
        delay.append(dataObj[packetId][RXTIME] - dataObj[packetId][TXTIME])
    return delay

def computeOutage(dataObj):
    delay = []
    for packetId in dataObj:
        delay.append(dataObj[packetId][RXTIME] - dataObj[packetId][TXTIME])
    return np.sum(np.array(delay) > 2 * 0.016)

def stopCondition(channelObj):
    for key in channelObj:
        if channelObj[key][0][DATA] != {}:
            return False
    return True


def testGlobalTimer():
    currentTimer = 0
    channelObj = initChannelObj()
    rxChannelObj = initChannelObj()
    # generatePacketTemplate(channelObj[G5][0][DATA], 0, DATALEN, 0)
    generatePacketTemplate(channelObj[G24][0][DATA], 0, DATALEN, 0)
    channelObj[G24].update(initTxObjs(1))
    generatePacketTemplate(channelObj[G24][1][DATA], 0, DATALEN, 0)
    counter = 1
    currentTimer, collisionFlag = selectTimer(channelObj, currentTimer)
    channelId = list(channelObj.keys())[0]
    txId = list(channelObj[channelId].keys())[0]
    packetId = [[0 , 0], [0 , 0]]
    interference = 1
    macQueue = 1
    while (stopCondition(channelObj) == False):
        txTime = dataLenToTime(macQueue, 600)
        if transferTxDataByTxId(txId, channelObj[channelId], rxChannelObj[channelId], packetId[channelId][txId], macQueue, currentTimer + txTime, collisionFlag) == 1:
            if currentTimer <= 10:
                packetId[channelId][txId] += 1
                if txId == 0:
                    generatePacketTemplate(channelObj[channelId][txId][DATA], 0.016 * packetId[channelId][txId], DATALEN, packetId[channelId][txId])
                else:
                    generatePacketTemplate(channelObj[channelId][txId][DATA], currentTimer - 0.01, DATALEN, packetId[channelId][txId])
                counter += 1
        currentTimer += txTime
        (currentTimer, collisionFlag) = selectTimer(channelObj, currentTimer)
        channelId = list(channelObj.keys())[0]
        txId = list(channelObj[channelId].keys())[0]

    print(currentTimer)
    # import matplotlib.pyplot as plt
    delay = computeDelay(rxChannelObj[G24][0][DATA])
    print(len(delay))
    print(len(computeDelay(rxChannelObj[G24][1][DATA])))
    from lqr_plot import cdf_plot
    import matplotlib.pyplot as plt
    cdf_plot(plt, delay)
    print(computeOutage(rxChannelObj[G24][0][DATA]))
    print(np.mean(delay))
    plt.show()

    # plt.show()
import time
start_time = time.time()
testGlobalTimer()
print("--- %s seconds ---" % (time.time() - start_time))