import logging
import math
import operator
import random
import warnings

import numpy as np

from packets import packets


class encoder():

    def generate(self, srcPkts: packets):
        '''
        Generate packets
        '''
        pkt_num = len(srcPkts.packets)
        pkt_ind = [i for i in range(pkt_num)]
        c, delta = 0.025, 0.05
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
        d_set = [i for i in range(1, len(mu) + 1)]
        d = np.random.choice(d_set, p=mu) + 1
        print(d)
        return d

    def robustSoliton(self, c, delta, k):
        rho = [0] * k
        rho[0] = 1 / k
        for d in range(2, k + 1):
            rho[d - 1] = 1 / (d * (d - 1))

        R = c * math.log(k / delta) * math.sqrt(k)
        d_max = math.floor(k / R)
        if d_max > k:
            logging.error("Parameter setting for robust soliton distribution is improper. Please change the setting (c, delta).")
            exit()
        tau = [0] * k
        for d in range(1, d_max):
            try:
                tau[d - 1] = R / (d * k)
            except:
                print(d)
        tau[d_max - 1] = R * math.log(R / delta) / k

        beta = sum(rho + tau)
        mu = [0] * k
        for d in range(k):
            mu[d] = (rho[d] + tau[d]) / beta

        return mu
