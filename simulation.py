import os

import numpy as np
import matplotlib.pyplot as plt


from packets import upper_packets
from encoder import encoder
from decoder import decoder


abs_path = os.path.dirname(os.path.abspath(__file__))


class tx:
    def __init__(self, tx_mcs=240, data_threshold=-1) -> None:
        self.tx_mcs = tx_mcs
        self.sended_data = 0
        self.data_threshold = data_threshold

        self.app_packet_counter = 0
        self.ip_packet_counter = 0

        self.backoff_counter = 0
        self.aifs = 2
        self.cw_min = 7
        self.cw_max = 1023
        self.cw_used = self.cw_min
        self.tx_failed = False

        self.mac_queue_length = 1
        self.packet_duration_list = []

        self.tx_packets = upper_packets()
        self.rx_packets = upper_packets()


        self.packet_encode = encoder()

        self.current_transmission_packet = []


    def try_tx(self, current_time):
        if not self.is_tx_finish():
            if self.backoff_counter == -self.aifs:
                if self.tx_failed:
                    self.cw_used = min(self.cw_max, self.cw_used * 2)
                else:
                    self.cw_used = self.cw_min
                self.backoff_counter = np.random.randint(0, self.cw_used)
                self.current_transmission_packet.clear()
                while len(self.current_transmission_packet) < self.mac_queue_length:
                    try:
                        current_app_packet = self.tx_packets.get_packet(
                            self.app_packet_counter
                        )
                    except:
                        if self.data_threshold == -1:
                            current_app_packet = self.tx_packets._generate_packets(0, "test" * 100)
                            # print(current_app_packet)
                        else:
                            print("packet not found")
                            break
                    if current_time > current_app_packet.get_time(0):
                        current_ip_data = current_app_packet.get_ip_packet(
                            self.ip_packet_counter
                        )
                        if current_ip_data == None:
                            self.app_packet_counter += 1
                            self.ip_packet_counter = 0
                            continue
                        self.current_transmission_packet.append(current_ip_data)
                        self.ip_packet_counter += 1
                    else:
                        break

            else:
                self.backoff_counter -= 1
            if self.backoff_counter == -self.aifs:
                return 1
        return 0

    def start_tx(self, current_time):
        tx_time = self.mac_queue_length * 1500 * 8 / (self.tx_mcs * 1e6)
        if not self.is_tx_finish():
            self.sended_data += self.mac_queue_length * 1500 * 8
            for packet in self.current_transmission_packet:
                self.packet_duration_list.append(current_time + tx_time)
                # self.rx_packets.update(self.packet_counter, current_time + tx_time)
                if packet is not None:
                    self.rx_packets.update_packet(
                        self.app_packet_counter,
                        packet,
                        current_time + tx_time,
                    )
                
                # self.packet_encode.decode(self.rx_packets, current_time + tx_time, self.tx_packets.get_data(self.packet_counter))
        return tx_time

    def is_tx_finish(self):
        if self.data_threshold > -1:
            return self.sended_data >= self.data_threshold or self.app_packet_counter >= self.tx_packets.max_packet_id
        return False


class env:
    def __init__(self, txs) -> None:
        self.txs = txs
        self.compete_interval = 20e-6
        self.status = "idle"
        self.current_time = 0

    def set_tx_failed(self, tx_suc, tx_id: bool):
        for tx_idx, tx in enumerate(self.txs):
            if tx_suc[tx_idx] == 1:
                tx.tx_failed = tx_id

    def _step(self):
        tx_suc = []
        send_tx = None
        for tx in self.txs:
            tx_suc.append(tx.try_tx(self.current_time))
            if tx_suc[-1] == 1:
                send_tx = tx
        if sum(tx_suc) > 1:
            self.status = "busy"
            self.set_tx_failed(tx_suc, True)
        elif sum(tx_suc) == 1:
            self.set_tx_failed(tx_suc, False)
            self.status = "tx"
            return send_tx.start_tx(self.current_time)
        else:
            self.status = "idle"
        return self.compete_interval

    def step(self):
        self.current_time += self._step()
        pass


if __name__ == "__main__":
    print("test")
    packet_src_data = "test" * 100
