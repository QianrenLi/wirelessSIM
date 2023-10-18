from packets import packets
import operator
class decoder():
    def __init__(self):
        self.rxData = []
        self.decPkts = packets()

    def decode(self, rx_queue: packets, rx_counter, srcPkts:packets):
        '''
        Determine the rx queue is correct or not based on data
        '''
        rx_newPktData = rx_queue.get_data(rx_counter)
        neighborID = rx_newPktData['neighbor_ids']
        d = len(neighborID)
        if d == 1:
            self.BP(self.rxData)
        else:
            self.rxData.append(rx_newPktData)
        src_num = len(srcPkts.packets)
        if len(self.decPkts.packets) == src_num:
            return self.dataVerification(srcPkts.packets, self.decPkts.packets)
        return None

    def BP(self, rxData):
        flag = False
        for pktData in self.rxData:
            neighbor_id = pktData['neighbor_ids']
            d = len(neighbor_id)
            if d == 0:
                self.rxData.remove(pktData)
            elif d == 1:
                flag = True
                self.decPkts.update(neighbor_id, pktData['payload'])
                neighbor_id_temp = neighbor_id
                payload_temp = pktData['payload']
                self.rxData.remove(pktData)
                for otherPktData in self.rxData:
                    if neighbor_id_temp in otherPktData['neighbor_ids']:
                        otherPktData['neighbor_ids'].remove(neighbor_id_temp)
                        otherPktData['payload'] = operator.xor(otherPktData['payload'], payload_temp)

        if flag:
            self.BP(self.rxData)
        return

    def dataVerification(self, srcPkts, decPkts):
        pkt_num = len(srcPkts)
        success = 0
        for i in range(pkt_num):
            srcPkt = srcPkts[i]
            decPkt = decPkts[i]
            if srcPkt.get_data().equals(decPkt.get_data()):
                success += 1
        success_rate = success / pkt_num
        failure_rate = 1 - success_rate
        return success_rate, failure_rate