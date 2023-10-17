import numpy as np
import matplotlib.pyplot as plt 
times = [140.1078176498413, 142.09760785102844, 144.0140631198883, 145.9929301738739,145.9929301738739, 145.9929301738739 ]

stuck_nums = [142.96666666666667, 152.4, 156.88333333333333, 161.55833333333334, 171.01666666666668, 184.95833333333334]



plt.plot( [50,52,54,56,58, 60] ,np.array(stuck_nums) / np.array(times))
plt.plot([50,52,54,56,58, 60], [190.66666666666666 / 134.41608834266663] * 6)
plt.xlabel("N1")
plt.ylabel("Stuck Frequency (num/s)")
plt.legend(["double_interface", "single_interface"])
plt.show()