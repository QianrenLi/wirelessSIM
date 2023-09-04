class packets():
    def __init__(self) -> None:
        self.time_stamp = {}

    def update(self, packet_id,time):
        self.time_stamp.update({packet_id:time})

    def sort(self):
        self.time_stamp = dict(sorted(self.time_stamp.items(), key=lambda item: item[1]))

    def __str__(self) -> str:
        return str(self.time_stamp)