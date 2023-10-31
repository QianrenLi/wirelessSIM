import pcapng
import struct
import numpy as np

def read_pcapng_file(file_path):
    time_slots = []
    packet_lengths = []

    with open(file_path, 'rb') as pcapng_file:
        blocks = pcapng.FileScanner(pcapng_file)

        for block in blocks:
            if isinstance(block, pcapng.blocks.EnhancedPacket):
                timestamp = block.timestamp
                length = block.packet_len
                time_slots.append(timestamp)
                packet_lengths.append(length)

    return time_slots, packet_lengths

def collectTimePacket(time_slots, packet_lengths, duration = 30):
    time_packet = []
    start_time = time_slots[0]
    last_time = time_slots[0]
    last_packet = packet_lengths[0]
    for i in range(0, len(time_slots)):
        ## aggregate
        if args.aggregate > 0 and (time_slots[i] - last_time) < args.aggregate:
            last_packet += packet_lengths[i]
            continue 
        ## millisecond, byte
        if int(last_packet) > 0:
            time_packet.append([int((time_slots[i] - last_time) * 1e9), int(last_packet)]) 
        last_time = time_slots[i] ; last_packet = 0
        if time_slots[i] - start_time > duration:
            break
    return np.array(time_packet)

def main(args):
    time_slots, packet_lengths = read_pcapng_file(args.pcapng_file)
    time_packet = collectTimePacket(time_slots, packet_lengths, args.duration)
    np.save(args.output_file, time_packet)

def configArg():
    import configargparse
    parser = configargparse.ArgumentParser(description='pcapng to npy')
    parser.add_argument('--config', is_config_file=True, help='config file path')
    parser.add_argument('--pcapng_file', type=str, help='pcapng file path')
    parser.add_argument('--output_file', type=str, help='output file path')
    parser.add_argument('--duration', type=int,  default = 30, help='time duration')
    parser.add_argument('--aggregate', type=float, default = 0 , help='aggregate time (s)')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = configArg()
    main(args)