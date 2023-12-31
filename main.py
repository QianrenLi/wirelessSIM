from simulation import tx
from simulation import env
from tqdm import tqdm
from qos import qosHandler
from packets import upper_packets
from encoder import encoder
from decoder import decoder
import matplotlib.pyplot as plt
import numpy as np
import random
import string
from lqr_plot import *
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


def single_interface(total_packets):
    txs_5G = [
        tx(tx_mcs=600, data_threshold=0),
        # tx(tx_mcs=600),
        # tx(tx_mcs=600)
    ]
    env_5G = env(txs_5G)
    env_5G.if_id = 0.3
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
    import matplotlib.pyplot as plt
    from lqr_plot import cdf_plot
    cdf_plot(plt,qosHandler._calc_delay(qos_handler.tx_queue, qos_handler.rx_queue))
    plt.show()
    del qos_handler.tx_queue, qos_handler.rx_queue
    return qos_handler

def double_interface(tx_packet_5G, tx_packet_2_4G, if_id = 0.3):
    txs_5G = [
        tx(tx_mcs=600, data_threshold=0),
        # tx(tx_mcs=600),
        # tx(tx_mcs=600),
    ]
    txs_2_4G = [
        tx(tx_mcs=150, data_threshold=0),
        # tx(tx_mcs=150),
        # tx(tx_mcs=150),
        # tx(tx_mcs=150),
    ]
    txs_5G[0].tx_packets, txs_2_4G[0].tx_packets = tx_packet_5G, tx_packet_2_4G
    env_5G = env(txs_5G)
    env_5G.if_id = 0.3
    env_2_4G = env(txs_2_4G)
    env_2_4G.if_id = 0
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

def dynamicN2Solver(simulation_time, epsilon, packetSplit, n1 = 38, n2 = 38, packet_num = 30 * 30, solverType = 2, folderInd = 2, epsilon2 = 0.001, is_control_stop = False):
    """
    Heuristic Solver to solve the optimization problem in control packet number.
    Hint: note that two parameter can be changed to influence the interference, contention situation.
    1. The MCS value, which generally influence the time take the transmit data
    2. The contention device
    3. The interference index (which represent the probability to loss random packet)

    Args:
        simulation_time (_type_): _description_
        epsilon (_type_): _description_
        packetSplit (_type_): _description_
        n1 (int, optional): _description_. Defaults to 38.
        n2 (int, optional): _description_. Defaults to 38.
        packet_num (_type_, optional): _description_. Defaults to 30*30.
        solverType (int, optional): _description_. Defaults to 2.
        folderInd (int, optional): _description_. Defaults to 2.
        epsilon2 (float, optional): _description_. Defaults to 0.001.
        is_control_stop (bool, optional): _description_. Defaults to False.

    Returns:
        _type_: _description_
    """
    ## create folder if not exist
    def fileSetup(folderInd):
        import os
        if not os.path.exists(f"./fig/{folderInd}"):
            os.makedirs(f"./fig/{folderInd}")
        if not os.path.exists(f"./log/{folderInd}"):
            os.makedirs(f"./log/{folderInd}")

    def N2Solver(latencyCh1, latencyCh2, epsilon):
        if latencyCh1 - latencyCh2 > epsilon:
            return -1
        elif latencyCh1 - latencyCh2 < -epsilon:
            return 1
        else:
            return 0
        
    def N1Solver(probCh1, probCh2, epsilon1, epsilon2):
        a = 0; b = 0
        if probCh1 > epsilon1:
            a = 1
        if probCh2 > epsilon1:
            b = -1
        if probCh1 < epsilon2:
            a = -1
        if probCh2 < epsilon2:
            b = 1
        return a, b

    def simuBase(tx_packet_5G, tx_packet_2_4G, prob = False, if_id = 0.1):
        MCS5G = 150
        MCS24G = int(MCS5G / 3)
        if if_id == 0:
            txs_5G: list[tx] = [
                tx(tx_mcs=MCS5G, data_threshold=0),
                # tx(tx_mcs=600),
            ]
        if if_id == 0.1:
            txs_5G = [
                tx(tx_mcs=MCS5G, data_threshold=0),
                tx(tx_mcs=MCS5G * 1.5),
                # tx(tx_mcs=600),
            ]
        if if_id == 0.2:
            txs_5G = [
                tx(tx_mcs=MCS5G, data_threshold=0),
                tx(tx_mcs=MCS5G * 1.5),
                tx(tx_mcs=MCS5G * 1.5),
                # tx(tx_mcs=600),
            ]

        txs_2_4G = [
            tx(tx_mcs=MCS24G, data_threshold=0),
            # tx(tx_mcs=150),
            # tx(tx_mcs=150),
            # tx(tx_mcs=150),
        ]
        txs_5G[0].tx_packets, txs_2_4G[0].tx_packets = tx_packet_5G, tx_packet_2_4G
        env_5G = env(txs_5G)
        env_5G.if_id = 0.00
        env_2_4G = env(txs_2_4G)
        env_2_4G.if_id = 0.00
        while True:
            if env_5G.txs[0].is_tx_finish() and env_2_4G.txs[0].is_tx_finish():
                break
            else:
                env_5G.step()
                env_2_4G.step()
        qos_5G = qosHandler(env_5G.txs[0].tx_packets, env_5G.txs[0].rx_packets)
        qos_2_4G = qosHandler(env_2_4G.txs[0].tx_packets, env_2_4G.txs[0].rx_packets)
        env_5G.txs[0].tx_packets.integrate(env_2_4G.txs[0].tx_packets)
        _ = env_5G.txs[0].rx_packets.integrate(env_2_4G.txs[0].rx_packets, probe = prob)
        qos_sys = (
            qosHandler()
            .update_packets(env_5G.txs[0].tx_packets, env_5G.txs[0].rx_packets)
            .handle(SERIOUS_STUCK)
            .handle(STUCK)
            .handle(AVERAGE_STUCK_DURATION)
            .handle(STUCK_FREQUENCY)
            .handle(JITTER)
        )
        if prob:
            return qos_sys, qos_5G, qos_2_4G, _[1]
        return qos_sys, qos_5G, qos_2_4G
    
    def Phase1(n2):
        # n2 = 50
        n2_list = []; latency5G_list = []; latency_2_4G_list = []; latency_list = []
        for _ in range(simulation_time):
            total_packets = generate_packets(path = "./data/proj_6.25MB.npy", packet_num = packet_num)
            tx_packet_5G, tx_packet_2_G = packetSplit(n2, n2, total_packets)
            del total_packets
            if_ind = 0.2 if _ >= 50 else 0.1
            if _ >= 100:
                if_ind = 0.1
            qos_handlers = simuBase(tx_packet_5G, tx_packet_2_G, if_id = if_ind)
            del tx_packet_5G, tx_packet_2_G
            latencyCh1 = qos_handlers[1].mean_delay ; latencyCh2 = qos_handlers[2].mean_delay
            n2_list.append(n2); latency5G_list.append(latencyCh1); latency_2_4G_list.append(latencyCh2); latency_list.append(qos_handlers[0].mean_delay)
            print(latencyCh1, latencyCh2)
            direction = N2Solver(latencyCh1, latencyCh2, epsilon) if not is_control_stop else 0
            n2 += direction
            print(n2)

        line_plot(plt, range(len(n2_list)), n2_list)
        plt.xlabel("Trials")
        plt.ylabel("N2-value")
        # plt.show()
        plt.savefig(f"./fig/{folderInd}/N2.pdf", format = 'pdf', dpi = 300)

        plt.figure()
        # line_plot(plt, range(len(n2_list)), np.array(latency5G_list) * 1000, label= "5G")
        # line_plot(plt, range(len(latency_2_4G_list)), np.array(latency_2_4G_list) * 1000, style='-o', label = "2.4G")
        line_plot(plt, range(len(latency_list)), np.array(latency_list) * 1000, style='--', label="System")
        plt.xlabel("Trials")
        plt.ylabel("Latency (ms)")
        plt.legend()
        plt.savefig(f"./fig/{folderInd}/Latency.pdf", format = 'pdf', dpi = 300)

        import csv
        ## save data to csv
        with open(f'./log/{folderInd}/N2.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['N2', 'latency5G', 'latency2.4G', 'latency'])
            for i in range(len(n2_list)):
                writer.writerow([n2_list[i], latency5G_list[i], latency_2_4G_list[i], latency_list[i]])

        return n2

    def Optimum(n1 ,n2):
        n1_list = []; n2_list = []; latency5G_list = []; latency_2_4G_list = []; latencys = []

        total_packets = generate_packets(path = "./data/proj_6.25MB.npy", packet_num = packet_num)
        tx_packet_5G, tx_packet_2_G = packetSplit(n1, n2, total_packets)
        del total_packets
        qos_handlers = simuBase(tx_packet_5G, tx_packet_2_G)
        del tx_packet_5G, tx_packet_2_G
        latencyCh1 = qos_handlers[1].mean_delay ; latencyCh2 = qos_handlers[2].mean_delay
        n1_list.append(n1); n2_list.append(n2); latency5G_list.append(latencyCh1); latency_2_4G_list.append(latencyCh2); latencys.append(qos_handlers[0].mean_delay)
        import csv
        with open(f'./log/{folderInd}/N1N2_latency.csv', 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['N1', 'N2', 'latency'])
            for i in range(len(n1_list)):
                writer.writerow([n1_list[i], n2_list[i], latencys[i]])
        pass
    
    def Phase2(n1, n2):
        def compute_prob(indexes, n1, n2):
            return np.sum((np.array(indexes) == n2)) / len(indexes), np.sum((np.array(indexes) == n1 + 1)) / len(indexes)
        # n2 = 37
        n2_list = [];  n1_list = []; outage_ch1_list = [] ;  outage_ch2_list = [] ; latencys = []
        delayListInitial = []; delayListStationary = []
        for _ in range(simulation_time):
            total_packets = generate_packets(path = "./data/proj_6.25MB.npy", packet_num = packet_num)
            tx_packet_5G, tx_packet_2_G = packetSplit(n1, n2, total_packets)
            del total_packets
            ##
            if_ind = 0.2 if _ >= 50 else 0.1
            if _ >= 100:
                if_ind = 0.1
            ##
            qos_handlers = simuBase(tx_packet_5G, tx_packet_2_G, prob = True, if_id = if_ind)
            del tx_packet_5G, tx_packet_2_G
            latency = qos_handlers[0].mean_delay
            if _ == 0:
                delayListInitial = qos_handlers[0].delayList
            elif _ == simulation_time - 1:
                delayListStationary = qos_handlers[0].delayList
            n2_list.append(n2); latencys.append(latency); n1_list.append(n1)
            print(latency)
            prob_cha1, prob_cha2 = compute_prob(qos_handlers[3], n1, n2)
            outage_ch1_list.append(prob_cha1); outage_ch2_list.append(prob_cha2)
            print(prob_cha1, prob_cha2)
            a,b = N1Solver(prob_cha1, prob_cha2, epsilon, epsilon2) if not is_control_stop else (0 , 0)
            n2 += a
            n1 += b

        ## CDF plot delay
        import matplotlib.pyplot as plt
        from lqr_plot import cdf_plot
        cdf_plot(plt, delayListInitial * 1000, label = "Initial", color = (243/255, 162/255, 97/255))
        cdf_plot(plt, delayListStationary * 1000, label = "Stationary")
        plt.xlabel("Latency (ms)")
        plt.ylabel("CDF")
        plt.legend()
        plt.savefig(f"./fig/{folderInd}/probDelay.pdf", format = 'pdf', dpi = 300)

        ## plot the N1 and N2
        plt.figure()
        line_plot(plt, range(len(n2_list)), n2_list, label= "N2")
        line_plot(plt, range(len(n1_list)), n1_list, label= "N1")
        plt.xlabel("Trials")
        plt.ylabel("N1-N2-value")
        plt.legend()
        plt.savefig(f"./fig/{folderInd}/N1prob.pdf", format = 'pdf', dpi = 300)

        ## plot the minimum latency
        plt.figure()
        line_plot(plt, range(len(n2_list)), np.array(latencys) * 1000)
        plt.xlabel("Trials")
        plt.ylabel("Latency (ms)")
        plt.savefig(f"./fig/{folderInd}/probLatency.pdf", format = 'pdf', dpi = 300)

        ## plot the outage probability
        plt.figure()
        line_plot(plt, range(len(n2_list)), np.array(outage_ch1_list), label= "5G")
        line_plot(plt, range(len(n1_list)), np.array(outage_ch2_list), label= "2.4G")
        plt.xlabel("Trials")
        plt.ylabel("Touch Boundary Probability")
        plt.legend()
        plt.savefig(f"./fig/{folderInd}/probOutage.pdf", format = 'pdf', dpi = 300)

        ## save data to csv
        import csv
        with open(f'./log/{folderInd}/probN1N2.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['N1', 'N2', 'latency', 'probCh1', 'probCh2'])
            for i in range(len(n2_list)):
                writer.writerow([n1_list[i], n2_list[i], latencys[i], outage_ch1_list[i], outage_ch2_list[i]])
        pass

    fileSetup(folderInd)
    if solverType == 1:
        return Phase1(n2)
    elif solverType == 2:
        return Optimum(n1,n2)
    elif solverType == 3:
        return Phase2(n1, n2)

def bunchSolver(input_tuples, packet_split_based_on_n1_n2, folderInd, packetNum):
    for tupleVal in input_tuples:
        dynamicN2Solver(50, 0.0006, packet_split_based_on_n1_n2, n1 = tupleVal[0], n2 = tupleVal[1], solverType = 2, folderInd = folderInd, packet_num= packetNum)

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
    

    # n2 = dynamicN2Solver(100, 0.0005, packet_split_based_on_n1_n2, packet_num = 30, solverType = 1, folderInd=14, epsilon2 = 0.001)
    # dynamicN2Solver(150, 0.02, packet_split_based_on_n1_n2, packet_num = 30, solverType = 3, folderInd=15, epsilon2 = 0.001, n1 = n2, n2 = n2)
    # dynamicN2Solver(150, 0.02, packet_split_based_on_n1_n2, packet_num = 30, solverType = 3, folderInd=16, epsilon2 = 0.001, is_control_stop=True, n1 = n2, n2 = n2)
    ## 
    dynamicN2Solver(150, 0.0005, packet_split_based_on_n1_n2, packet_num = 30, solverType = 1, folderInd=17, epsilon2 = 0.001, n1 = 37, n2 = 37)

    # dynamicN2Solver(50, 0.001, packet_split_based_on_n1_n2, packet_num = 30, solverType = 1)

    # input_dicts = []
    # for n1 in range(38, 28, -1):
    #     for n2 in range(38, 48):
    #         input_dicts.append((n1,n2))
    # cpu_num = 32
    # import multiprocessing
    # ## split the input_dicts into cpu_num parts and run each with solver
    # input_dicts_list = []
    # for i in range(cpu_num):
    #     input_dicts_list.append([])
    # for i in range(len(input_dicts)):
    #     input_dicts_list[i % cpu_num].append(input_dicts[i])
    # print(input_dicts_list)
    # processes = []
    # folderInd = 5; packetNum = 30 * 30 * 10
    # for _ in range(cpu_num):
    #     p = multiprocessing.Process(target=bunchSolver, args=(input_dicts_list[_], packet_split_based_on_n1_n2, folderInd, packetNum))
    #     p.start()
    #     processes.append(p)
    # for p in processes:
    #     p.join()


    # qos_handlers_double_interface = []
    # x_vals = []
    # redundance_tuple =(0, 10, 1)
    # testing_num = 1
    # packet_num = 30 * 30 ## 30s simulation
    # for redundance in tqdm(range(redundance_tuple[0], redundance_tuple[1], redundance_tuple[2])):
    #     random.seed(0)
    #     _qos_handlers_double_interface = []
    #     for trial in tqdm(range(testing_num)):
    #         n1 = n2 - redundance
    #         total_packets = generate_packets(path = "./data/proj_6.25MB.npy", packet_num = packet_num)
    #         tx_packet_5G, tx_packet_2_G = packet_split_based_on_n1_n2(n1, n2, total_packets)
    #         del total_packets
    #         qos_handler = double_interface(tx_packet_5G, tx_packet_2_G)
    #         del tx_packet_5G, tx_packet_2_G
    #         # print(qos_handler)
    #         _qos_handlers_double_interface.append(qos_handler)
    #     x_vals.append(n1)
    #     ## average the qos_handler result
    #     qos_handler = qosHandler()
    #     for att in ATTRIBUTE:
    #         val = 0
    #         for _qos_handler in _qos_handlers_double_interface:
    #             val += getattr(_qos_handler, att)
    #         setattr(qos_handler, att, val / len(_qos_handlers_double_interface))
    #     qos_handler.stuck_frequency = qos_handler.stuck_num / qos_handler.interval
    #     qos_handlers_double_interface.append(qos_handler)
    #     print(qos_handler)

    
    # qos_handlers_single_interface = []
    # _qos_handlers_double_interface = []
    # random.seed(0)
    # for trial in tqdm(range(testing_num)):
    #     total_packets = generate_packets(path = "./data/proj_6.25MB.npy", packet_num = packet_num)
    #     qos_handler = single_interface(total_packets)
    #     del total_packets
    #     # print(qos_handler)
    #     _qos_handlers_double_interface.append(qos_handler)
    # for att in ATTRIBUTE:
    #     val = 0
    #     for _qos_handler in _qos_handlers_double_interface:
    #         val += getattr(_qos_handler, att)
    #     setattr(qos_handler, att, val / len(_qos_handlers_double_interface))
    # qos_handler.stuck_frequency = qos_handler.stuck_num / qos_handler.interval
    # print(qos_handler)

    # for redundance in range(redundance_tuple[0], redundance_tuple[1], redundance_tuple[2]):
    #     qos_handlers_single_interface.append(qos_handler)

    # for att, _title, ylabel in zip(ATTRIBUTE, TITLES, YLABLE):
    #     vals = []
    #     for qos_handler in qos_handlers_double_interface:
    #         vals.append(getattr(qos_handler, att))
    #     ## plot the result
    #     import matplotlib.pyplot as plt
        
    #     plt.plot(x_vals, vals, label = "double_interface")
    #     print(vals)

    #     vals = []
    #     for qos_handler in qos_handlers_single_interface:
    #         vals.append(getattr(qos_handler, att))
    #     plt.plot(x_vals, vals, label = "single_interface")

    #     plt.title(_title)
    #     plt.xlabel("n1")
    #     plt.ylabel(_title + "(" + ylabel + ")")

    #     plt.legend()    
    #     plt.savefig(f"./fig/{_title}.png")
    #     plt.close()