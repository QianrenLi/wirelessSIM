TIME = "time"
DATA = "data"


class packets:
    def __init__(self) -> None:
        self.packets = {}

    def update(self, packet_id, time, data=None):
        self.packets.update({packet_id: {TIME: time, DATA: data}})

    def sort(self):
        self.packets = dict(
            sorted(self.packets.items(), key=lambda item: item[0])
        )
    
    def get_data(self, packet_id):
        if packet_id in self.packets:
            return self.packets[packet_id][DATA]
        return None

    def get_time(self, packet_id):
        if packet_id in self.packets:
            return self.packets[packet_id][TIME]
        return None

    def __str__(self) -> str:
        return str(self.packets)
