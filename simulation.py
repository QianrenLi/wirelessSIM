import os

import numpy as np
import matplotlib.pyplot as plt

from tqdm import tqdm

from packets import packets

from criteria import qosHandler
from criteria import (
    STUCK,
    SERIOUS_STUCK,
    JITTER,
    AVERAGE_STUCK_DURATION,
    STUCK_FREQUENCY,
)

abs_path = os.path.dirname(os.path.abspath(__file__))


class tx:
    def __init__(self, tx_mcs=240, data_threshold=-1) -> None:
        self.tx_mcs = tx_mcs
        self.sended_data = 0
        self.data_threshold = data_threshold

        self.packet_counter = 0
        self.backoff_counter = 0
        self.aifs = 2
        self.cw_min = 7
        self.cw_max = 1023
        self.cw_used = self.cw_min
        self.tx_failed = False

        self.mac_queue_length = 1
        self.packet_duration_list = []

        self.tx_packets = packets()
        self.rx_packets = packets()

    def try_tx(self, current_time):
        if not self.is_tx_finish():
            if self.backoff_counter == -self.aifs:
                if self.tx_failed:
                    self.cw_used = min(self.cw_max, self.cw_used * 2)
                else:
                    self.cw_used = self.cw_min
                self.backoff_counter = np.random.randint(0, self.cw_used)
                self.packet_counter += 1
                self.tx_packets.update(self.packet_counter, current_time)
            else:
                self.backoff_counter -= 1
            if self.backoff_counter == -self.aifs:
                return 1
        return 0

    def start_tx(self, current_time):
        tx_time = self.mac_queue_length * 1500 * 8 / (self.tx_mcs * 1e6)
        if not self.is_tx_finish():
            self.sended_data += self.mac_queue_length * 1500 * 8
            for i in range(self.mac_queue_length):
                self.packet_duration_list.append(current_time + tx_time)
                self.rx_packets.update(self.packet_counter, current_time + tx_time)
        return tx_time

    def is_tx_finish(self):
        if self.data_threshold > -1:
            return self.sended_data >= self.data_threshold
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
    total_packet_num = 70
    n1 = 40
    n2 = 50
    mean_delay = []
    variance = []

    for redundance in [0, 2, 5, 8, 10]:
        n1 = n2 - redundance
        packet_num_5G = n2
        packet_num_2_4G = total_packet_num - n1
        # print(packet_num_5G * 1500 * 8 / (600 * 1e6))
        # exit()
        durations = []
        for i in tqdm(list(range(100))):
            txs_5G = [
                tx(tx_mcs=600, data_threshold=packet_num_5G * 1500 * 8),
                tx(tx_mcs=600),
            ]
            txs_2_4G = [
                tx(tx_mcs=150, data_threshold=packet_num_2_4G * 1500 * 8),
                tx(tx_mcs=150),
            ]
            env_5G = env(txs_5G)
            env_2_4G = env(txs_2_4G)

            while True:
                if env_5G.txs[0].is_tx_finish() and env_2_4G.txs[0].is_tx_finish():
                    break
                else:
                    env_5G.step()
                    env_2_4G.step()

            possible_duration = []
            minimum_5G_packet = 0
            minimum_duration = 10
            print(env_5G.txs[0].tx_packets)
            print(env_5G.txs[0].rx_packets)
            qos_handler = (
                qosHandler()
                .update_packets(env_5G.txs[0].tx_packets, env_5G.txs[0].rx_packets)
                .handle(SERIOUS_STUCK)
                .handle(STUCK)
                .handle(AVERAGE_STUCK_DURATION)
                .handle(STUCK_FREQUENCY)
                .handle(JITTER)
            )
            print(qos_handler)

            exit()
            for packet_idx, duration_5G in enumerate(
                env_5G.txs[0].packet_duration_list
            ):
                left_packet = total_packet_num - (packet_idx + 2)
                if left_packet > 0 and left_packet < len(
                    env_2_4G.txs[0].packet_duration_list
                ):
                    possible_duration.append(
                        max(
                            duration_5G,
                            env_2_4G.txs[0].packet_duration_list[left_packet],
                        )
                    )
                    if minimum_duration > max(
                        duration_5G, env_2_4G.txs[0].packet_duration_list[left_packet]
                    ):
                        minimum_5G_packet = packet_idx
                        minimum_duration = max(
                            duration_5G,
                            env_2_4G.txs[0].packet_duration_list[left_packet],
                        )
            durations.append(min(possible_duration) * 1000)

        from lqr_plot import cdf_plot
        from lqr_plot import pmf_plot
        from lqr_plot import twin_ax_legend

        # cdf_plot(duration_5G, "5G")
        fig, ax1 = plt.subplots(figsize=(9, 6))
        ax2 = ax1.twinx()
        steps = 0.1
        bins = np.arange(0, 15, steps)
        lns1 = pmf_plot(ax1, durations, labels="PMF", bins=bins, normalized=True)
        lns2 = cdf_plot(ax2, durations, "CDF", color="darkorange")
        twin_ax_legend(ax2, hist=[lns1], plot=[lns2], loc="upper right")
        ax1.set_title("n1-%d, n2-%d" % (n1, n2))
        ax1.set_xlabel("Transmission Duration(ms)")
        ax1.set_ylabel("PMF")
        ax2.set_ylabel("CDF")
        plt.grid(axis="y", ls="--", alpha=0.8)
        plt.show()
        plt.savefig(
            abs_path + "/fig/Redundance-%d.png" % (n2 - n1),
            bbox_inches="tight",
            format="png",
            dpi=300,
        )
        plt.close()

        # mean_delay.append(np.mean(durations))
        # print(mean_delay)
        # variance.append(np.var(durations))

    # plt.plot(n2 - np.array([0, 2, 5, 8, 10]), mean_delay)
    # plt.xlabel("N1")
    # plt.ylabel("Mean Delay(ms)")
    # plt.savefig(abs_path + "/fig/mean_delay.png",bbox_inches = 'tight', format = 'png', dpi = 300)
    # plt.close()
    # plt.plot(n2 - np.array([0, 2, 5, 8, 10]), variance)
    # plt.xlabel("N1")
    # plt.ylabel("Variance")
    # plt.savefig(abs_path + "/fig/variance.png",bbox_inches = 'tight', format = 'png', dpi = 300)
    # plt.close()
