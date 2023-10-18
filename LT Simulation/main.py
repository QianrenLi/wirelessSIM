from simulation import tx
from simulation import env
from qos import qosHandler
from qos import (
    STUCK,
    SERIOUS_STUCK,
    JITTER,
    AVERAGE_STUCK_DURATION,
    STUCK_FREQUENCY,
)

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