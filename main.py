from simulation import tx
from simulation import env
from tqdm import tqdm
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
ATTRIBUTE = ["stuck_duration","stuck_num" , "serious_stuck_duration", "serious_stuck_num", "average_stuck_duration", "stuck_frequency", "jitter", "stuck_frequency","mean_delay","interval"]
TITLES = ["Stuck Duration", "Stuck Num" , "Serious Stuck Duration", "Serious Stuck Num", "Average Stuck Duration", "Stuck Frequency", "Jitter", "Stuck Frequency","Mean Delay", "Interval"]
YLABLE = ["s", "num" , "s", "num", "s", "num/s", "s", "num/s","s", "s"]

def generate_packets(**kwargs):
    if "path" in kwargs:
        def generate_packet_from_file(path, packet_num):
            data = np.load(path)
            duration = data[0][0] / 1e9 # s
            app_packet_size = data[0][1] # B
            ## app_packet_size = 1200
            packets = upper_packets()
            for i in range(packet_num):
                # packets.generate_packets(i * duration, i, ''.join(random.choices(string.ascii_uppercase + string.digits, k=app_packet_size)))
                packets.generate_packets(i * duration, i, ''.join('0'*app_packet_size))
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

def single_interface(total_packets):
    txs_5G = [
        tx(tx_mcs=600, data_threshold=0),
        tx(tx_mcs=600),
        tx(tx_mcs=600),
        # tx(tx_mcs=600),
    ]
    env_5G = env(txs_5G)
    txs_5G[0].tx_packets = total_packets
    while True:
        if env_5G.txs[0].is_tx_finish():
            break
        else:
            env_5G.step()
    qos_handler = (
        qosHandler()
        .update_packets(env_5G.txs[0].tx_packets, env_5G.txs[0].rx_packets)
        .handle(SERIOUS_STUCK)
        .handle(STUCK)
        .handle(AVERAGE_STUCK_DURATION)
        .handle(STUCK_FREQUENCY)
        .handle(JITTER)
    )
    del qos_handler.tx_queue, qos_handler.rx_queue
    return qos_handler

def double_interface(tx_packet_5G, tx_packet_2_4G):
    txs_5G = [
        tx(tx_mcs=600, data_threshold=0),
        tx(tx_mcs=600),
        tx(tx_mcs=600),
        # tx(tx_mcs=600),
        # tx(tx_mcs=600),
    ]
    txs_2_4G = [
        tx(tx_mcs=150, data_threshold=0),
        tx(tx_mcs=150),
        # tx(tx_mcs=150),
        # tx(tx_mcs=150),
        # tx(tx_mcs=150),
    ]
    txs_5G[0].tx_packets, txs_2_4G[0].tx_packets = tx_packet_5G, tx_packet_2_4G
    env_5G = env(txs_5G)
    env_2_4G = env(txs_2_4G)
    while True:
        if env_5G.txs[0].is_tx_finish() and env_2_4G.txs[0].is_tx_finish():
            break
        else:
            env_5G.step()
            env_2_4G.step()
    env_5G.txs[0].tx_packets.integrate(env_2_4G.txs[0].tx_packets)
    env_5G.txs[0].rx_packets.integrate(env_2_4G.txs[0].rx_packets)
    qos_handler = (
        qosHandler()
        .update_packets(env_5G.txs[0].tx_packets, env_5G.txs[0].rx_packets)
        .handle(SERIOUS_STUCK)
        .handle(STUCK)
        .handle(AVERAGE_STUCK_DURATION)
        .handle(STUCK_FREQUENCY)
        .handle(JITTER)
    )
    del qos_handler.tx_queue, qos_handler.rx_queue
    return qos_handler

if __name__ == "__main__":
    def packet_split_based_on_n1_n2(n1,n2, packets:upper_packets):
        packets_5G = upper_packets()
        packets_2_4G = upper_packets()
        ## split each packet into two packets
        for packet_id in packets.packets:
            packet = packets.get_packet(packet_id)
            ip_packet_2_4G, ip_packet_5G = packet.split(n1 = n1, n2 = n2)
            ip_packet_2_4G.update_time( 10, packets.get_time(packet_id))
            packets_5G.update(packet_id, packets.get_time(packet_id) ,ip_packet_5G)
            packets_2_4G.update(packet_id,packets.get_time(packet_id) , ip_packet_2_4G)
        return packets_5G, packets_2_4G
    # test = generate_packets(path = "./data/proj_6.25MB.npy", packet_num = 5)
    # a, b = packet_split_based_on_n1_n2(40, 50, test)
    # a.integrate(b)
    # exit()
    random.seed(0)
    total_packet_num = 70
    n1 = 40
    n2 = 60

    qos_handlers_double_interface = []
    x_vals = []
    redundance_tuple =(0, 10, 1)
    testing_num = 100000
    for redundance in tqdm(range(redundance_tuple[0], redundance_tuple[1], redundance_tuple[2])):
        _qos_handlers_double_interface = []
        for trial in tqdm(range(testing_num)):
            n1 = n2 - redundance
            total_packets = generate_packets(path = "./data/proj_6.25MB.npy", packet_num = 10)
            tx_packet_5G, tx_packet_2_G = packet_split_based_on_n1_n2(n1, n2, total_packets)
            del total_packets
            qos_handler = double_interface(tx_packet_5G, tx_packet_2_G)
            del tx_packet_5G, tx_packet_2_G
            # print(qos_handler)
            _qos_handlers_double_interface.append(qos_handler)
        x_vals.append(n1)
        ## average the qos_handler result
        qos_handler = qosHandler()
        for att in ATTRIBUTE:
            val = 0
            for _qos_handler in _qos_handlers_double_interface:
                val += getattr(_qos_handler, att)
            setattr(qos_handler, att, val / len(_qos_handlers_double_interface))
        qos_handler.stuck_frequency = qos_handler.stuck_num / qos_handler.interval
        qos_handlers_double_interface.append(qos_handler)
        print(qos_handler)

    
    qos_handlers_single_interface = []
    _qos_handlers_double_interface = []
    for trial in tqdm(range(testing_num)):
        total_packets = generate_packets(path = "./data/proj_6.25MB.npy", packet_num = 10)
        qos_handler = single_interface(total_packets)
        del total_packets
        # print(qos_handler)
        _qos_handlers_double_interface.append(qos_handler)
    for att in ATTRIBUTE:
        val = 0
        for _qos_handler in _qos_handlers_double_interface:
            val += getattr(_qos_handler, att)
        setattr(qos_handler, att, val / len(_qos_handlers_double_interface))
    qos_handler.stuck_frequency = qos_handler.stuck_num / qos_handler.interval
    print(qos_handler)

    for redundance in range(redundance_tuple[0], redundance_tuple[1], redundance_tuple[2]):
        qos_handlers_single_interface.append(qos_handler)

    for att, _title, ylabel in zip(ATTRIBUTE, TITLES, YLABLE):
        vals = []
        for qos_handler in qos_handlers_double_interface:
            vals.append(getattr(qos_handler, att))
        ## plot the result
        import matplotlib.pyplot as plt
        
        plt.plot(x_vals, vals, label = "double_interface")
        print(vals)

        vals = []
        for qos_handler in qos_handlers_single_interface:
            vals.append(getattr(qos_handler, att))
        plt.plot(x_vals, vals, label = "single_interface")

        plt.title(_title)
        plt.xlabel("n1")
        plt.ylabel(_title + "(" + ylabel + ")")

        plt.legend()    
        plt.savefig(f"./fig/{_title}.png")
        plt.close()