from simulation import tx
from simulation import env
from qos import qosHandler
from packets import upper_packets
from encoder import encoder
from decoder import decoder
import numpy as np
import random
import string
from qos import (
    STUCK,
    SERIOUS_STUCK,
    JITTER,
    AVERAGE_STUCK_DURATION,
    STUCK_FREQUENCY,
)

def generate_packets(**kwargs):
    if "path" in kwargs:
        def generate_packet_from_file(path, packet_num):
            data = np.load(path)
            duration = data[0][0] / 1e9 # s
            app_packet_size = data[0][1] # B
            packets = upper_packets()
            for i in range(packet_num):
                packets.generate_packets(i * duration, i, ''.join(random.choices(string.ascii_uppercase + string.digits, k=app_packet_size)))
            return packets
        if "packet_num" not in kwargs:
            return generate_packet_from_file(kwargs["path"], 1000)
        return generate_packet_from_file(kwargs["path"], kwargs["packet_num"])
    else:
        packets = upper_packets()
        time_delta = 1e-3
        for i in range(1000):
            packets.generate_packets(i * time_delta, i, "test" * 10000)
        return packets
    

def encode_test():
    packets = generate_packets()
    encode = encoder()
    packets.get_data(0)
    print(encode.generate(packets.get_packet(0)))

def decode_test():
    packets =  generate_packets()
    encode = encoder()
    decode = decoder()
    encoded_packets = encode.generate(packets.get_packet(0))
    assert(decode.decode(encoded_packets) == packets)

# encode_test()
# decode_test()
# exit()

if __name__ == "__main__":
    def packet_split_based_on_n1_n2(n1,n2, packets:upper_packets):
        packets_5G = upper_packets()
        packets_2_4G = upper_packets()
        ## split each packet into two packets
        for packet_id in packets.packets:
            packet = packets.get_packet(packet_id)
            ip_packet_2_4G, ip_packet_5G = packet.split(n1 = n1, n2 = n2)
            packets_5G.update(packet_id,ip_packet_5G.get_time(0) ,ip_packet_5G)
            packets_2_4G.update(packet_id,ip_packet_5G.get_time(0) , ip_packet_2_4G)
        return packets_5G, packets_2_4G
    test = generate_packets(path = "./data/proj_6.25MB.npy", packet_num = 5)
    a, b = packet_split_based_on_n1_n2(40, 50, test)
    a.integrate(b)

    total_packet_num = 70
    n1 = 40
    n2 = 500
    mean_delay = []
    variance = []
    for redundance in [0, 2, 5, 8, 10]:
        n1 = n2 - redundance
        packet_num_5G = n2
        packet_num_2_4G = total_packet_num - n1
        durations = []
        txs_5G = [
            tx(tx_mcs=600, data_threshold=packet_num_5G * 1500 * 8),
            tx(tx_mcs=600),
        ]
        txs_5G[0].tx_packets = generate_packets()
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