from cdflib import CDF, cdfepoch
import matplotlib.pyplot as plt
import numpy as np

filename = "psp_fld_l2_mag_rtn_1min_20181106_v02.cdf"

cdf = CDF(filename)

epoch = cdf.varget("epoch_mag_RTN_1min")
times = cdfepoch.to_datetime(epoch)

B = cdf.varget("psp_fld_l2_mag_RTN_1min")

BR = B[:, 0]
BT = B[:, 1]
BN = B[:, 2]

Bmag = np.sqrt(BR**2 + BT**2 + BN**2)

plt.figure(figsize=(12, 7))

plt.plot(times, BR, label="B_R")
plt.plot(times, BT, label="B_T")
plt.plot(times, BN, label="B_N")
plt.plot(times, Bmag, label="|B|", linewidth=2)

plt.xlabel("Time")
plt.ylabel("Magnetic field [nT]")
plt.title("Parker Solar Probe FIELDS — 2018-11-06")

plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()