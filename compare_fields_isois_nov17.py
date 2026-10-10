from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from cdflib import CDF, cdfepoch


# ============================================================
# FIND FILES
# ============================================================

folder = Path(".")

fields_matches = list(
    folder.glob(
        "psp_fld_l2_mag_rtn_1min_20181117_*.cdf"
    )
)

isois_matches = list(
    folder.glob(
        "psp_isois-epihi_l2-let1-rates3600_20181117_*.cdf"
    )
)

if not fields_matches:
    raise FileNotFoundError(
        "Could not find Nov 17 FIELDS file."
    )

if not isois_matches:
    raise FileNotFoundError(
        "Could not find Nov 17 IS☉IS LET1 hourly file."
    )

fields_file = fields_matches[0]
isois_file = isois_matches[0]

print("\nUsing files:")
print("FIELDS:", fields_file.name)
print("IS☉IS :", isois_file.name)


# ============================================================
# OPEN FILES
# ============================================================

fields = CDF(str(fields_file))
isois = CDF(str(isois_file))


# ============================================================
# FIELDS — MAGNETIC FIELD
# ============================================================

fields_epoch = fields.varget(
    "epoch_mag_RTN_1min"
)

fields_time = cdfepoch.to_datetime(
    fields_epoch
)

B = np.asarray(
    fields.varget(
        "psp_fld_l2_mag_RTN_1min"
    ),
    dtype=float
)

# Remove actual invalid/fill values
B[
    (~np.isfinite(B))
    | (np.abs(B) > 1e20)
] = np.nan

BR = B[:, 0]
BT = B[:, 1]
BN = B[:, 2]

Bmag = np.sqrt(
    BR**2
    + BT**2
    + BN**2
)


# ============================================================
# IS☉IS — PROTON / HYDROGEN RATE
# ============================================================

variable = "A_H_Rate"

if variable not in isois.cdf_info().zVariables:
    raise RuntimeError(
        f"{variable} not found in IS☉IS file."
    )

attrs = isois.varattsget(variable)

proton_rate = np.asarray(
    isois.varget(variable),
    dtype=float
)

isois_epoch_name = attrs["DEPEND_0"]

isois_epoch = isois.varget(
    isois_epoch_name
)

isois_time = cdfepoch.to_datetime(
    isois_epoch
)


# ============================================================
# CLEAN IS☉IS DATA
#
# IMPORTANT:
# Zero is a valid measurement.
# Only fill values / invalid values are removed.
# ============================================================

valid = np.isfinite(proton_rate)

fill_value = attrs.get("FILLVAL")

if fill_value is not None:

    fill_value = float(
        np.asarray(fill_value).flatten()[0]
    )

    valid &= ~np.isclose(
        proton_rate,
        fill_value,
        rtol=0,
        atol=0
    )

clean_rate = np.where(
    valid,
    proton_rate,
    np.nan
)


# ============================================================
# SUM THE 25 PROTON ENERGY CHANNELS
#
# This gives us a simple proton-activity proxy.
# ============================================================

proton_activity = np.nansum(
    clean_rate,
    axis=1
)

# Do not convert completely missing timestamps into zero
valid_time = valid.reshape(
    valid.shape[0],
    -1
).any(axis=1)

proton_activity[
    ~valid_time
] = np.nan


# ============================================================
# BASIC INFORMATION
# ============================================================

print("\nFIELDS:")
print("Measurements:", len(fields_time))
print("Cadence: ~1 minute")

print("\nIS☉IS:")
print("Measurements:", len(isois_time))
print("Proton-rate shape:", proton_rate.shape)
print("Cadence: ~1 hour")

print(
    "\nMean proton activity:",
    np.nanmean(proton_activity),
    "counts/s"
)

print(
    "Maximum proton activity:",
    np.nanmax(proton_activity),
    "counts/s"
)


# ============================================================
# FIND PARTICLE PEAK
# ============================================================

peak_index = np.nanargmax(
    proton_activity
)

peak_time = isois_time[
    peak_index
]

peak_rate = proton_activity[
    peak_index
]

print("\nPeak proton activity:")
print("Time:", peak_time)
print("Rate:", peak_rate, "counts/s")


# ============================================================
# PLOT
# ============================================================

fig, (ax1, ax2) = plt.subplots(
    2,
    1,
    figsize=(15, 9),
    sharex=True,
    gridspec_kw={
        "height_ratios": [1.4, 1]
    }
)


# ============================================================
# TOP — FIELDS
# ============================================================

ax1.plot(
    fields_time,
    BR,
    label="B_R"
)

ax1.plot(
    fields_time,
    BT,
    label="B_T"
)

ax1.plot(
    fields_time,
    BN,
    label="B_N"
)

ax1.plot(
    fields_time,
    Bmag,
    label="|B|",
    linewidth=2
)

ax1.set_ylabel(
    "Magnetic field [nT]"
)

ax1.set_title(
    "Parker Solar Probe — FIELDS + IS☉IS\n"
    "Energetic Proton Event — 2018-11-17"
)

ax1.legend(
    loc="upper right"
)

ax1.grid(
    True,
    alpha=0.3
)


# ============================================================
# BOTTOM — IS☉IS
# ============================================================

ax2.plot(
    isois_time,
    proton_activity,
    marker="o",
    linewidth=2,
    label="LET1 H proton activity"
)

ax2.set_ylabel(
    "Summed count rate [counts/s]"
)

ax2.set_xlabel(
    "Time"
)

ax2.legend(
    loc="upper left"
)

ax2.grid(
    True,
    alpha=0.3
)


# ============================================================
# MARK THE PROTON PEAK ON BOTH PANELS
# ============================================================

ax1.axvline(
    peak_time,
    linestyle="--",
    alpha=0.7,
    label="Proton peak"
)

ax2.axvline(
    peak_time,
    linestyle="--",
    alpha=0.7
)


# ============================================================
# TIME AXIS
# ============================================================

ax2.xaxis.set_major_locator(
    mdates.HourLocator(
        interval=2
    )
)

ax2.xaxis.set_major_formatter(
    mdates.DateFormatter(
        "%H:%M"
    )
)


# ============================================================
# FINISH
# ============================================================

plt.tight_layout()

plt.show()