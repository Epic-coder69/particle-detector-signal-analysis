from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from cdflib import CDF, cdfepoch


# ============================================================
# FIND FILES
# ============================================================

folder = Path(".")

nov6_files = list(
    folder.glob(
        "psp_isois-epihi_l2-let1-rates60_20181106_*.cdf"
    )
)

nov17_files = list(
    folder.glob(
        "psp_isois-epihi_l2-let1-rates3600_20181117_*.cdf"
    )
)

if not nov6_files:
    raise FileNotFoundError(
        "Could not find Nov 6 LET1 rates60 file."
    )

if not nov17_files:
    raise FileNotFoundError(
        "Could not find Nov 17 LET1 rates3600 file."
    )

nov6_file = nov6_files[0]
nov17_file = nov17_files[0]

print("\nFILES")
print("=" * 70)
print("Nov 6 :", nov6_file.name)
print("Nov 17:", nov17_file.name)


# ============================================================
# OPEN CDF FILES
# ============================================================

cdf6 = CDF(str(nov6_file))
cdf17 = CDF(str(nov17_file))


# ============================================================
# VARIABLE WE WANT
# ============================================================

variable = "A_H_Rate"

vars6 = cdf6.cdf_info().zVariables
vars17 = cdf17.cdf_info().zVariables

if variable not in vars6:
    raise RuntimeError(
        f"{variable} not found in Nov 6 file."
    )

if variable not in vars17:
    print("\nA_H_Rate was NOT found in the Nov 17 file.")
    print("\nVariables containing 'H' and 'Rate':")

    for name in vars17:
        if "H" in name and "Rate" in name:
            print(name)

    raise RuntimeError(
        "Cannot compare until we identify the correct Nov 17 proton-rate variable."
    )


print("\nVARIABLE")
print("=" * 70)
print(variable)

print("\nNov 6 description:")
print(cdf6.varattsget(variable))

print("\nNov 17 description:")
print(cdf17.varattsget(variable))


# ============================================================
# HELPER FUNCTION FOR MISSING DATA
# ============================================================

def clean_variable(cdf, variable):

    data = np.asarray(
        cdf.varget(variable),
        dtype=float
    )

    attrs = cdf.varattsget(variable)

    valid = np.isfinite(data)

    fill = attrs.get("FILLVAL")

    if fill is not None:

        fill_values = np.asarray(fill).flatten()

        for value in fill_values:

            try:
                value = float(value)

                valid &= ~np.isclose(
                    data,
                    value,
                    rtol=0,
                    atol=0
                )

            except (ValueError, TypeError):
                pass

    # IMPORTANT:
    # zero is VALID.
    # We only remove actual missing/fill data.
    clean = np.where(
        valid,
        data,
        np.nan
    )

    return clean, valid, attrs


# ============================================================
# LOAD PROTON RATE DATA
# ============================================================

rate6, valid6, attrs6 = clean_variable(
    cdf6,
    variable
)

rate17, valid17, attrs17 = clean_variable(
    cdf17,
    variable
)


print("\nDATA SHAPES")
print("=" * 70)

print("Nov 6 :", rate6.shape)
print("Nov 17:", rate17.shape)


# ============================================================
# LOAD TIME
# ============================================================

epoch_name6 = attrs6["DEPEND_0"]
epoch_name17 = attrs17["DEPEND_0"]

epoch6 = cdf6.varget(epoch_name6)
epoch17 = cdf17.varget(epoch_name17)

time6 = cdfepoch.to_datetime(epoch6)
time17 = cdfepoch.to_datetime(epoch17)


print("\nTIME RECORDS")
print("=" * 70)

print("Nov 6 :", len(time6))
print("Nov 17:", len(time17))


# ============================================================
# LOAD ENERGY AXES
# ============================================================

energy_name6 = attrs6.get("DEPEND_1")
energy_name17 = attrs17.get("DEPEND_1")

energy6 = None
energy17 = None

if energy_name6 is not None:
    energy6 = np.asarray(
        cdf6.varget(energy_name6),
        dtype=float
    )

if energy_name17 is not None:
    energy17 = np.asarray(
        cdf17.varget(energy_name17),
        dtype=float
    )


print("\nENERGY INFORMATION")
print("=" * 70)

print("Nov 6 energy variable :", energy_name6)
print("Nov 17 energy variable:", energy_name17)

if energy6 is not None:
    print("Nov 6 energy shape:", energy6.shape)

if energy17 is not None:
    print("Nov 17 energy shape:", energy17.shape)


# ============================================================
# SUM ALL HYDROGEN ENERGY CHANNELS
#
# A_H_Rate is counts/sec in multiple energy channels.
#
# We sum channels at each time to create one simple
# "total LET1 proton activity" time series.
# ============================================================

if rate6.ndim == 1:
    total6 = rate6.copy()
else:
    total6 = np.nansum(rate6, axis=1)

if rate17.ndim == 1:
    total17 = rate17.copy()
else:
    total17 = np.nansum(rate17, axis=1)


# If an entire timestamp was missing,
# don't turn it into a fake zero.

valid_time6 = valid6.reshape(
    valid6.shape[0],
    -1
).any(axis=1)

valid_time17 = valid17.reshape(
    valid17.shape[0],
    -1
).any(axis=1)

total6[~valid_time6] = np.nan
total17[~valid_time17] = np.nan


# ============================================================
# STATISTICS
# ============================================================

def summarize(label, data, valid, total, times):

    valid_values = data[valid]

    nonzero = valid_values > 0

    print("\n")
    print("=" * 70)
    print(label)
    print("=" * 70)

    print(
        "Valid cells:",
        f"{100 * np.sum(valid) / valid.size:.2f}%"
    )

    print(
        "Non-zero among valid cells:",
        f"{100 * np.sum(nonzero) / len(valid_values):.2f}%"
    )

    finite_total = total[
        np.isfinite(total)
    ]

    active_times = np.sum(
        finite_total > 0
    )

    print(
        "Valid timestamps:",
        len(finite_total)
    )

    print(
        "Timestamps with proton activity:",
        active_times
    )

    print(
        "Mean summed proton rate:",
        np.mean(finite_total)
    )

    print(
        "Median summed proton rate:",
        np.median(finite_total)
    )

    print(
        "Maximum summed proton rate:",
        np.max(finite_total)
    )

    max_index = np.nanargmax(total)

    print(
        "Strongest timestamp:",
        times[max_index]
    )

    print(
        "Rate at strongest timestamp:",
        total[max_index]
    )

    return {
        "mean": np.mean(finite_total),
        "median": np.median(finite_total),
        "max": np.max(finite_total),
        "active_fraction":
            100 * active_times / len(finite_total)
    }


stats6 = summarize(
    "2018-11-06 — LET1 1-minute",
    rate6,
    valid6,
    total6,
    time6
)

stats17 = summarize(
    "2018-11-17 — LET1 1-hour",
    rate17,
    valid17,
    total17,
    time17
)


# ============================================================
# DIRECT COMPARISON
# ============================================================

print("\n")
print("=" * 70)
print("NOV 17 VS NOV 6")
print("=" * 70)

if stats6["mean"] > 0:

    print(
        "Mean activity ratio:",
        stats17["mean"] / stats6["mean"]
    )

if stats6["max"] > 0:

    print(
        "Peak activity ratio:",
        stats17["max"] / stats6["max"]
    )

print(
    "Active timestamp fraction Nov 6:",
    f'{stats6["active_fraction"]:.2f}%'
)

print(
    "Active timestamp fraction Nov 17:",
    f'{stats17["active_fraction"]:.2f}%'
)


# ============================================================
# PLOT
# ============================================================

fig, (ax1, ax2) = plt.subplots(
    2,
    1,
    figsize=(14, 8)
)


# Nov 6
ax1.plot(
    time6,
    total6
)

ax1.set_title(
    "IS☉IS EPI-Hi LET1 — Hydrogen/Proton Activity — 2018-11-06"
)

ax1.set_ylabel(
    "Summed count rate [counts/s]"
)

ax1.grid(
    True,
    alpha=0.3
)


# Nov 17
ax2.plot(
    time17,
    total17,
    marker="o"
)

ax2.set_title(
    "IS☉IS EPI-Hi LET1 — Hydrogen/Proton Activity — 2018-11-17"
)

ax2.set_ylabel(
    "Summed count rate [counts/s]"
)

ax2.set_xlabel(
    "Time"
)

ax2.grid(
    True,
    alpha=0.3
)


# ============================================================
# TIME FORMAT
# ============================================================

for ax in (ax1, ax2):

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%H:%M")
    )

    ax.xaxis.set_major_locator(
        mdates.HourLocator(interval=3)
    )


plt.tight_layout()
plt.show()