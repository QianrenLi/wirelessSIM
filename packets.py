TIME = "time"
DATA = "data"
PAYLOAD = "payload"
ORIGINAL_ID = "original_id"
import copy
DATA_ABSTRACT = True

class packets:
    def __init__(self, packets = {}) -> None:
        self.packets = packets
        self.max_packet_id = 0

    def update(self, packet_id, time, data=None, original_id = None):
        # data : {"payload": payload}
        _time = self.packets[packet_id][TIME] if time == None and packet_id in self.packets else time
        _data = self.packets[packet_id][DATA] if data == None and packet_id in self.packets else copy.copy(data)
        if original_id is not None:
            self.packets.update({packet_id: {TIME: _time, DATA: _data, ORIGINAL_ID: original_id}})
        else:
            self.packets.update({packet_id: {TIME: _time, DATA: _data}})
        self.max_packet_id = max(self.max_packet_id, packet_id)
        

    def sort(self):
        self.packets = dict(
            sorted(self.packets.items(), key=lambda item: item[0])
        )
        return self
    
    def get_ip_packet(self, packet_id):
        if packet_id in self.packets:
            return {packet_id:self.packets[packet_id]}
        return None
    
    
    def get_data(self, packet_id):
        if packet_id in self.packets:
            return self.packets[packet_id][DATA]
        raise Exception("Packet not exist")
        return None

    def get_time(self, packet_id):
        if packet_id in self.packets:
            return self.packets[packet_id][TIME]
        return None
    
    def get_maximum_time(self):
        maximum_time = 0
        for packet_id in self.packets:
            if self.get_time(packet_id) > maximum_time:
                maximum_time = self.get_time(packet_id)
        return maximum_time
    
    def get_maximum_time_index(self):
        maximum_time = 0
        maximum_time_index = 0
        for packet_id in self.packets:
            if self.get_time(packet_id) > maximum_time:
                maximum_time = self.get_time(packet_id)
                maximum_time_index = packet_id
        return maximum_time_index

    def update_time(self, packet_id, time):
        if packet_id in self.packets:
            self.packets[packet_id][TIME] = time
        return self
    
    def get_original_id(self, packet_id):
        if packet_id in self.packets:
            return self.packets[packet_id][ORIGINAL_ID]
        return None
    
    def remove(self, packet_id):
        if packet_id in self.packets:
            self.packets.pop(packet_id)
        pass
    
    def asdict(self) -> dict:
        return self.packets
    
    def integrate(self, packet : 'packets', probe = False):
        ## determine self and packets belong to same class
        if not isinstance(packet, type(self)):
            raise Exception("Integrate packets type not match")
            return None
        if isinstance(self, upper_packets):
            def recover_id(ip_packet: 'packets'):
                _packet = packets({})
                for packet_id in ip_packet.packets:
                    original_id = ip_packet.get_original_id(packet_id)
                    _packet.update(original_id, ip_packet.get_time(packet_id), ip_packet.get_data(packet_id), original_id= original_id)
                return _packet
            def integrate_by_original_id(A_packet:upper_packets, B_packet:upper_packets):
                idexs = []
                for _packet_id in B_packet.packets:
                    B_data = recover_id(B_packet.get_packet(_packet_id))
                    _ = A_packet.get_packet(_packet_id).integrate(B_data,probe)
                    idexs.append(_[1]) if probe else None
                    A_packet.update_time(_packet_id, A_packet.get_packet(_packet_id).get_maximum_time())
                if probe:
                    return A_packet, idexs
                return A_packet
            return integrate_by_original_id(self, packet)
        else:
            ## rename packet id in packets
            for packet_id, _packet in packet.asdict().items():
                ## select minimum time in self.packets
                _packet_time = min(self.get_time(packet_id), _packet[TIME]) if self.get_time(packet_id) else _packet[TIME]
                self.update(packet_id , _packet_time, _packet[DATA])
            if probe:
                return self, self.get_maximum_time_index()
            return self
    

    def split(self, **kwargs) -> 'packets':
        if "n1" in kwargs and "n2" in kwargs:
            n1 = kwargs["n1"]
            n2 = kwargs["n2"]
            assert(n1 in self.packets and n2 in self.packets)
            _packet_n1 = upper_packets({}) if isinstance(self, upper_packets) else packets({})
            ## iterate in reverse order
            ip_packet_id = 0
            for _packet_id, data in sorted(self.packets.items(), reverse=True):
                if _packet_id > n1:
                    _packet_n1.update(ip_packet_id, data[TIME], data[DATA], original_id= _packet_id)
                    ip_packet_id += 1


            _packet_n2 = upper_packets({}) if isinstance(self, upper_packets) else packets({})
            for _packet_id, data in self.packets.items():
                if _packet_id <= n2:
                    _packet_n2.update(_packet_id, data[TIME], data[DATA], original_id= _packet_id)
            return _packet_n1, _packet_n2

        elif "packet_id" in kwargs:
            packet_id = kwargs["packet_id"]
            if packet_id not in self.packets:
                raise Exception("Packet not exist")
                return None
            _packet = upper_packets({}) if isinstance(self, upper_packets) else packets({})
            for _packet_id, data in self.packets.items():
                if _packet_id >= packet_id:
                    _packet.update(_packet_id - packet_id, data[TIME], data)
            for _packet_id in list(self.packets.keys()):
                if _packet_id >= packet_id:
                    self.remove(_packet_id)
            return _packet
        else:
            raise Exception("Split packets error")
            return None
    


    def __str__(self) -> str:
        return str(self.packets)


class upper_packets(packets):
    
    HEADER_LEN = 20 # maximum 60 bytes
    PAYLOAD_LEN = 1500 - HEADER_LEN
    def __init__(self) -> None:
        super().__init__()
        self.packets = {}

    def update_packet(self, packet_id, data:dict, time):
        '''
        update ip packet to correspond app packet
        '''
        if packet_id not in self.packets:
            # raise Exception("Upper packets not exist")
            self.update(packet_id, time, packets(data))
        else:
            ## if original id exist:
            if ORIGINAL_ID in list(data.values())[0]:
                self.get_packet(packet_id).update(list(data.keys())[0], time, list(data.values())[0][DATA], original_id= list(data.values())[0][ORIGINAL_ID])
            else:
                self.get_packet(packet_id).update(list(data.keys())[0], time, list(data.values())[0][DATA])
            self.update(packet_id, time, self.get_packet(packet_id))
        return self

    def sort(self):
        return super().sort()
    
    def get_packet(self, packet_id) -> packets:
        return super().get_data(packet_id)
    
    def get_data(self, packet_id) -> bytes:
        payload = b''
        if packet_id not in self.packets:
            Exception("Upper packets not exist")
            return None
        packet = self.get_packet(packet_id).sort()
        if packet == None:
            Exception("IP packets not exist")
            return None
        for _packet_id, data in packet.packets.items():
            payload+=data[DATA][PAYLOAD]
        return payload

    @staticmethod
    def _generate_packets(time, payload):
        if type(payload) != str:
            raise Exception("Payload must be string")
            return None
        payload_byte = payload.encode("utf-8")
        _packet = packets({})
        _packet_id = 0
        while True:
            if DATA_ABSTRACT:
                _packet.update(_packet_id, time, {PAYLOAD: ''})
            else:
                _packet.update(_packet_id, time, {PAYLOAD: payload_byte[:upper_packets.PAYLOAD_LEN]})
            _packet_id += 1
            payload_byte = payload_byte[upper_packets.PAYLOAD_LEN:]
            if len(payload_byte) == 0:
                break
        return _packet

    @staticmethod
    def _correct_packets(payload_byte):
        return payload_byte.decode("utf-8")
    
    def generate_packets(self, time, packet_id, payload):
        _packet = self._generate_packets(time, payload)
        self.update(packet_id, time, _packet)
        return self
    
    
    def aggregate_packets(self) -> packets:
        '''
        for each ip_packets in upper packets, aggregate them into one ip_packet with payload and time, the packet_id is increase for each ip_packet
        '''
        _packet = packets({})
        _packet_id = 0
        for packet_id in self.packets:
            _packet.update(_packet_id, self.get_time(packet_id), {PAYLOAD: self.get_data(packet_id)})
            _packet_id += 1
        return _packet 
    
    def correct_packets(self, packet_id):
        return self._correct_packets(self.get_data(packet_id))
    

    def get_time(self, packet_id):
        return super().get_time(packet_id)

if __name__ == "__main__":
    def remove_test():
        packets = upper_packets()
        packets.generate_packets(0, 0, "test" * 10000)
        packets.generate_packets(0, 1, "test" * 10000)
        packets.generate_packets(0, 2, "test" * 10000)
        packets.remove(1)
        print(packets)
    def split_test():
        packets = upper_packets()
        packets.generate_packets(0, 0, "test" * 10000)
        packets.generate_packets(0, 1, "test" * 10000)
        packets.generate_packets(0, 2, "test" * 10000)
        print(packets)
        _ = packets.split(1)
        print(packets, _)
    def integrate_test():
        packets = upper_packets()
        packets.generate_packets(0, 0, "test" * 10000)
        packets.generate_packets(0, 1, "test" * 10000)
        packets.generate_packets(0, 2, "test" * 10000)
        packets2 = upper_packets()
        packets2.generate_packets(0, 0, "test" * 10000)
        packets2.generate_packets(0, 1, "test" * 10000)
        packets2.generate_packets(0, 2, "test" * 10000)
        packets.integrate(packets2)
        print(packets)
    def modify_test():
        packet = upper_packets()
        packet.generate_packets(0, 0, "test" * 10000)
        packet.generate_packets(0, 1, "test" * 10000)
        packet.generate_packets(0, 2, "test" * 10000)
        print(packet)
        packet.update(1, 0 , {0:packets()})
        print(packet)
        _ = packet.split(1)
        print(packet, _)
    # modify_test()