from simulation import tx
from simulation import env
from qos import qosHandler
from packets import upper_packets
from qos import (
    STUCK,
    SERIOUS_STUCK,
    JITTER,
    AVERAGE_STUCK_DURATION,
    STUCK_FREQUENCY,
)

def generate_packets():
    packets = upper_packets()
    time_delta = 1e-3
    for i in range(1000):
        packets.generate_packets(i * time_delta, i, "test" * 10)
    return packets

if __name__ == "__main__":
    total_packet_num = 700
    n1 = 40
    n2 = 500
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
        txs_5G[0].tx_packets = generate_packets()
        # print(txs_5G[0].packet_encode.generate(txs_5G[0].tx_packets))
        # txs_5G[1].tx_packets = generate_packets()
        txs_2_4G = [
            tx(tx_mcs=150, data_threshold=packet_num_2_4G * 1500 * 8),
            tx(tx_mcs=150),
        ]
        txs_2_4G[0].tx_packets = generate_packets()
        # txs_2_4G[1].tx_packets = generate_packets()
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
        # compare the data of tx packets and rx packets of packet

        print(env_5G.txs[0].tx_packets.get_data(0) == env_5G.txs[0].rx_packets.get_data(0))
        # print(env_5G.txs[0].rx_packets.get_data(0))
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