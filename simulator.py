import random
import copy
import numpy as np
# from txObj import txObj

IDLE = 0 ; BUSY = 1; COLLISION = 2
rx_5G_queue = []
rx_2_4G_queue = []

TIME_SLOT = 1e-5

event_list = []

class dataPhy():
    def __init__(self, id) -> None:
        self.frame = {}
        self.data_len = 0
        self.data_len_max = 5
        self.tx_id = id

    def add(self, data:dict):
        for _data in data:
            data_len = data[_data]["data"]
            if self.data_len + data_len > self.data_len_max and self.data_len != self.data_len_max:
                frame_data = copy.copy(data[_data])
                frame_data.update({"data": self.data_len_max - self.data_len})
                self.frame.update({_data : frame_data})
                self.data_len = self.data_len_max
            else:
                self.frame.update({_data : data[_data]})
                self.data_len += data_len

    def update_endtimer(self, timer):
        for key in self.frame:
            self.frame[key].update({"end_time": timer})


def compute_stuck_num(delay):
    stuck_num = 0
    for _delay in delay:
        if _delay* TIME_SLOT >= 2 * 16e-3:
            stuck_num += 1
    return stuck_num


class channelObj():
    def __init__(self) -> None:
        self.channel_5G = channelMac(MCS=600)
        self.channel_2_4G = channelMac(MCS=150)
        self.rx_time = []
        self.delay = []

    def determine_channel_status(self, txs, num = 1000):
        def determine_packet(rx_5G_queue, rx_2_4G_queue):
            delete_key = []
            for key in list(rx_5G_queue.keys()):
                if key in rx_2_4G_queue:
                    if rx_5G_queue[key]["data"] + rx_2_4G_queue[key]["data"] >= 68:
                        self.delay.append(max(rx_5G_queue[key]["end_time"] - rx_5G_queue[key]["start_time"], rx_2_4G_queue[key]["end_time"] - rx_2_4G_queue[key]["start_time"]))
                        rx_5G_queue.pop(key)
                        rx_2_4G_queue.pop(key)
                        delete_key.append(key)
            return delete_key

        txs_5G = [tx.tx_5G for tx in txs]
        txs_2_4G = [tx.tx_2_4G for tx in txs]
        while True:
            [tx.transmit(self) for tx in txs]
            self.channel_5G.determine_channel_status(txs_5G)
            self.channel_2_4G.determine_channel_status(txs_2_4G)
            [tx.distribute() for tx in txs]
            delete_key = determine_packet(self.channel_5G.rx_queue, self.channel_2_4G.rx_queue)
            [tx.delete_key(delete_key) for tx in txs]
            if len(self.delay) > num:
                break
        ## Print time slot
        assert(self.channel_5G.timer == self.channel_2_4G.timer)

        return compute_stuck_num(self.delay)
        

        


class channelMac():
    def __init__(self, MCS = 600) -> None:
        self.timer = 0
        self.tx_sent_frame = []
        self.rx_queue = {}
        self.delta_time_slot = 0
        self.MCS = MCS
        self.status = IDLE
        self.slot_time = TIME_SLOT
        self.delay = []
        self.interference_ratio = 0
    
    def data_to_time(self, data_len):
        tx_MCS = max(1 , self.MCS * (1 - random.random() * self.interference_ratio))
        
        return np.ceil((data_len * 1500 * 8 / (tx_MCS * 1e6)) / self.slot_time)

    def determine_channel_status(self, txs):
        if self.delta_time_slot == 0:
            if self.status == BUSY:
                # print(self.status)
                data = self.tx_sent_frame[0]
                for key in data.frame:
                    if key in self.rx_queue:
                        self.rx_queue[key]["data"] += data.frame[key]["data"]
                    else:
                        self.rx_queue.update({key : copy.copy(data.frame[key])})
                    self.rx_queue[key]["end_time"] = self.timer
                ## inform tx to delete data
                txs[data.tx_id].tx_success()
                self.tx_sent_frame.clear()
                self.status == IDLE
                ## wait for data append
                # print(self.delta_time_slot)
                # print("IDLE")
            if len(self.tx_sent_frame) > 0:
                # Get maximum data
                max_data = 0
                for data in self.tx_sent_frame:
                    if data is not None:
                        max_data = max(max_data, data.data_len)
                self.delta_time_slot = self.data_to_time(max_data)
                if len(self.tx_sent_frame) == 1:
                    self.status = BUSY
                    # print("BUSY")
                else:
                    self.status = COLLISION
                    # print("COLLISION")
            else:
                self.status = IDLE
                # print("IDLE")
                self.delta_time_slot = 1
        else:
            self.delta_time_slot -= 1

        self.timer += 1

    def compute_delay(self):
        if len(self.rx_queue) > 0:
            data = self.rx_queue.pop(0)
            for key in data.frame:
                _delay = data.frame[key]["end_time"] - data.frame[key]["start_time"]
                self.delay.append(_delay)

class txObj():
    def __init__(self, id = 0) -> None:
        self.arrival = 0.1
        self.timer = 0
        self.tx_5G = txObjMac(id)
        self.tx_2_4G = txObjMac(id)
        self.n1 = 50
        self.n2 = 60
        self.tx_id = 0
        self.packet_num = 68
        self.id = id
        self.data_tx_ed = False

    def distribute(self, interval = 1):
        for _ in range(interval):
            # if random.random() < self.arrival:
            if not self.data_tx_ed and self.timer * TIME_SLOT % 16e-3 < 8e-3:
                self.data_tx_ed = True
                self.tx_5G.generate_packets(start_time = self.timer, data = self.n2)
                self.tx_2_4G.generate_packets(start_time = self.timer, data = self.packet_num - self.n1)
            elif self.timer * TIME_SLOT % 16e-3 > 8e-3:
                self.data_tx_ed = False
            self.tx_id += 1
            self.timer += 1            
    
    def transmit(self, channel: channelObj):
        res = self.tx_5G.transmit(channel.channel_5G)
        res = self.tx_2_4G.transmit(channel.channel_2_4G)
    
    def delete_key(self, delete_key):
        self.tx_5G.delete_key(delete_key)
        self.tx_2_4G.delete_key(delete_key)




class txObjMac():
    class cwOpt():
        def __init__(self) -> None:
            self.aifs = 2
            self.cw_min = 7
            self.cw_max = 1023
            self.cw_used = self.cw_min
            self.cw_value = random.randint(0, self.cw_used)

        def update(self, tx_failed):
            if self.cw_value == -self.aifs:
                if tx_failed:
                    self.cw_used = min(self.cw_max, self.cw_used * 2)
                else:
                    self.cw_used = self.cw_min
                self.cw_value = random.randint(0, self.cw_used)
            else:
                self.cw_value -= 1
            return self.cw_value == -self.aifs
        
    def __init__(self, id) -> None:
        self.packet_id = 0
        self.id = id
        self.cw = self.cwOpt()
        self.tx_failed = False
        self.txing_data = None
        self.data = {}

    def generate_packets(self, data, start_time = None, end_time = None):
        self.packet_id += 1
        self.data.update(
            {self.packet_id: {
                "start_time": start_time, 
                "end_time":end_time,
                "data": data
                } 
            }
        )
    
    def get_data_len(self):
        return len(self.data)
    

    def transmit(self, channel: channelMac):
        def prepare_tx_data(data):
            data_frame = dataPhy(self.id)
            data_frame.add(data)
            return data_frame
        
        if channel.status == IDLE:
            if len(self.data) > 0:
                if self.cw.update(self.tx_failed):
                    self.txing_data = prepare_tx_data(self.data)
                    channel.tx_sent_frame.append(self.txing_data)
                    return 1
        return 0
    
    def tx_success(self):
        self.tx_failed = False
        for key in self.txing_data.frame:
            ## compare data length
            if key in self.data:
                res = self.txing_data.frame[key]["data"] - self.data[key]["data"]
                assert(res <= 0)
                if res == 0:
                    self.data.pop(key)
                else:
                    self.data[key]["data"] = -res
        self.txing_data = None

    def update_timer(self, timer):
        self.time_slot = timer

    def delete_key(self, delete_key):
        for key in delete_key:
            if key in self.data:
                self.data.pop(key)

import multiprocessing

def executor(pro_id, n1,  return_dit):
    stuck_nums = []
    durations = []
    for i in range(10):
        channel = channelObj()
        channel.channel_5G.interference_ratio = 1
        txs = [txObj(id) for id in range(1)]
        txs[0].n1 = n1
        stuck_num = channel.determine_channel_status(txs, 1000)
        stuck_nums.append(stuck_num)
        durations.append(channel.channel_5G.timer)
    return_dit[pro_id] = {"stuck_nums":stuck_nums, "durations": durations}
if __name__ == "__main__":
    # for n1 in range(50, 60):
    import time
    
    n1_stuck_nums = []
    n1_stuck_frequency = []
    for n1 in [54, 54, 54, 54, 54]:
        stuck_nums = []
        durations = []
        return_dit = multiprocessing.Manager().dict()
        processes = []
        for _ in range(12): 
            random.seed(0)
            for i in range(14):
                p = multiprocessing.Process(target=executor, args=(i, n1, return_dit, ))
                p.start()
                processes.append(p)
            for p in processes:
                p.join()

            for i in range(14):
                stuck_nums += return_dit[i]["stuck_nums"]
                durations += return_dit[i]["durations"]
        # print(stuck_nums)
        print("Stuck Num", np.mean(stuck_nums))
        n1_stuck_nums.append(np.mean(stuck_nums))
        print("Average Session Time", np.mean(durations) * TIME_SLOT)
        n1_stuck_frequency.append(np.mean(stuck_nums) / np.mean(durations) / TIME_SLOT)

    # print(n1_stuck_nums)
    # print(n1_stuck_frequency)
    # import matplotlib.pyplot as plt
    # plt.plot(range(50, 60), n1_stuck_frequency)
    # plt.xlabel("n1")
    # plt.ylabel("Stuck Frequency")
    # plt.show()