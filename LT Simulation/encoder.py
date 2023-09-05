import math
import operator
import random
import numpy as np

from packets import packets


class encoder():

    def generate(self, srcPkts: packets):
        '''
        Generate packets
        '''
        pkt_num = len(srcPkts.packets)
        pkt_ind = [i for i in range(pkt_num)]
        c, delta = 0.05, 0.05
        neighbor_num = self.degreeSelection(c, delta, pkt_num)

        neighbor_ids = random.sample(pkt_ind, neighbor_num)

        appData = None
        for neighbor_id in neighbor_ids:
            if not appData:
                appData = srcPkts.get_data(neighbor_id)
            else:
                appData = map(operator.xor, appData, srcPkts.get_data(neighbor_id))
        IPdata = {'neighbor_ids': neighbor_ids, 'payload': appData}
        return IPdata



    def degreeSelection(self, c, delta, k):
        mu = self.robustSoliton(c, delta, k)
        d_set = [i for i in range(1, len(mu))]
        d = np.random.choice(d_set, p=mu)
        return d

    def robustSoliton(self, c, delta, k):
        rho = [0] * k
        rho[0] = 1 / k
        for d in range(2, k):
            rho[d] = 1 / (d * (d - 1))

        R = c * math.log(k / delta) * math.sqrt(k)
        d_max = math.ceil(k / R)
        tau = [0] * d_max
        for d in range(d_max - 1):
            tau[d] = R / (d * k)
        tau[-1] = R * math.log(R / delta)

        beta = sum(rho + tau)
        mu = [0] * d_max
        for d in range(d_max):
            mu[d] = (rho[d] + tau[d]) / beta

        return mu
