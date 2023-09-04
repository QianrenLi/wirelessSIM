import numpy as np

STUCK = "stuck"
SERIOUS_STUCK = "serious stuck"
DURATION = "duration"
TIMER = "timer"
STUCK_DURATION = "stuck duration"
JITTER = "jitter"
AVERAGE_STUCK_DURATION = "average stuck duration"
STUCK_FREQUENCY = "stuck frequency"

QOSTYPE = (STUCK, SERIOUS_STUCK, JITTER, AVERAGE_STUCK_DURATION, STUCK_FREQUENCY)

from packets import packets
from packets import TIME


class qosHandler:
    def __init__(self) -> None:
        self.qos_type = None
        self.tx_queue = None
        self.rx_queue = None

        self.stuck_num = 0
        self.serious_stuck_num = 0

        self.stuck_duration = 0
        self.serious_stuck_duration = 0
        self.average_stuck_duration = 0

        self.interval = 0
        self.qos_type_struct = {
            "name": None,
            DURATION: 1,
            TIMER: 10,
            STUCK_DURATION: 0.2,
        }
        self.time_unit = "s"

    def update_packets(self, tx_queue: packets, rx_queue: packets):
        self.tx_queue = tx_queue
        self.rx_queue = rx_queue
        return self

    def __str__(self) -> str:
        return (
            f"stuck num: {self.stuck_num} (num)\nstuck duration: {self.stuck_duration} ({self.time_unit})\n"
            + f"serious stuck num: {self.serious_stuck_num} (num)\n"
            + f"serious stuck duration: {self.serious_stuck_duration} ({self.time_unit})\n"
            + f"mean delay: {self.mean_delay} ({self.time_unit})\njitter: {self.jitter} ({self.time_unit})\n"
            + f"average stuck duration: {self.average_stuck_duration} ({self.time_unit})\n"
            + f"stuck frequency: {self.stuck_frequency} (num/{self.time_unit})\n"
        )

    def handle(self, qos_type):
        self.qos_type = qos_type
        if qos_type == STUCK:
            return self.stuck_handle()
        elif qos_type == SERIOUS_STUCK:
            return self.serious_stuck_handle()
        elif qos_type == JITTER:
            return self.jitter_handle()
        elif qos_type == AVERAGE_STUCK_DURATION:
            return self.stuck_handle().average_stuck_duration_handle()
        elif qos_type == STUCK_FREQUENCY:
            return self.stuck_handle().stuck_frequency_handle()

    def average_stuck_duration_handle(self):
        self.average_stuck_duration = self.stuck_duration / self.stuck_num
        return self

    def stuck_frequency_handle(self):
        self.stuck_frequency = self.stuck_num / self.interval
        return self

    def stuck_handle(self):
        self.interval = self.tx_queue.time_stamp[max(self.tx_queue.time_stamp.keys())][TIME]
        tx_packet_diff, rx_packet_diff = self._calc_packet_diff(
            self.tx_queue, self.rx_queue
        )
        qos_type_struct = self.qos_type_struct
        qos_type_struct["name"] = STUCK
        self.stuck_num, self.stuck_duration = self._calc_qos_stuck(
            tx_packet_diff, rx_packet_diff, qos_type_struct
        )
        return self

    def serious_stuck_handle(self):
        tx_packet_diff, rx_packet_diff = self._calc_packet_diff(
            self.tx_queue, self.rx_queue
        )
        qos_type_struct = self.qos_type_struct
        qos_type_struct["name"] = SERIOUS_STUCK
        self.serious_stuck_num, self.serious_stuck_duration = self._calc_qos_stuck(
            tx_packet_diff, rx_packet_diff, qos_type_struct
        )
        return self

    def jitter_handle(self):
        delay = self._calc_delay(self.tx_queue, self.rx_queue)
        self.mean_delay = np.mean(delay)
        self.jitter = np.mean(abs(delay - self.mean_delay))
        return self

    @staticmethod
    def _calc_delay(tx_packets: packets, rx_packets: packets):
        tx_packets.sort()
        rx_packets.sort()
        delay = []
        for idx, entity in rx_packets.time_stamp.items():
            delay.append(entity[TIME] - tx_packets.time_stamp[idx][TIME]) if entity[TIME] is not None else None
        delay = np.array(delay)
        return delay

    @staticmethod
    def _calc_packet_diff(tx_packets: packets, rx_packets: packets):
        tx_packets.sort()
        rx_packets.sort()
        delay = []
        his_tx_timestamp = 0
        his_rx_timestamp = 0
        tx_packet_diff = []
        rx_packet_diff = []
        for idx, entity in rx_packets.time_stamp.items():
            if entity[TIME] is not None:
                rx_packet_diff.append(entity[TIME] - his_rx_timestamp)
                if idx not in tx_packets.time_stamp:
                    Exception("tx_packets and rx_packets are not match")
                    return
                tx_packet_diff.append(tx_packets.time_stamp[idx][TIME] - his_tx_timestamp)
                his_rx_timestamp = entity[TIME]
                his_tx_timestamp = tx_packets.time_stamp[idx][TIME]
        return tx_packet_diff, rx_packet_diff

    @staticmethod
    def _calc_qos_stuck(tx_packet_diff, rx_packet_diff, qos_type_struct):
        stuck_num = 0
        stuck_duration = 0
        serious_stuck_num = 0
        serious_stuck_duration = 0
        stuck_timer = 0
        stuck_duration = 0
        for i in range(len(tx_packet_diff)):
            if rx_packet_diff[i] > 2 * tx_packet_diff[i]:
                stuck_num += 1
                if stuck_duration < qos_type_struct[DURATION]:
                    stuck_timer += 1
                    stuck_duration += rx_packet_diff[i] - tx_packet_diff[i]
                    if stuck_timer >= qos_type_struct[TIMER]:
                        serious_stuck_num += 1
                        serious_stuck_duration += stuck_duration
                    elif stuck_duration >= qos_type_struct[STUCK_DURATION]:
                        serious_stuck_duration += stuck_duration
                stuck_duration += rx_packet_diff[i] - tx_packet_diff[i]
        if qos_type_struct["name"] == STUCK:
            return stuck_num, stuck_duration
        if qos_type_struct["name"] == SERIOUS_STUCK:
            return serious_stuck_num, serious_stuck_duration
