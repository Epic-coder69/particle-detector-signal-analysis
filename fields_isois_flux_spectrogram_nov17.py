from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from matplotlib.colors import LogNorm
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
# FIELDS DATA
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

# Remove invalid / fill values
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
# IS☉IS PROTON FLUX
# ============================================================

flux_variable = "A_H_Flux"
energy_variable = "H_ENERGY"

if flux_variable not in isois.cdf_info().zVariables:
    raise RuntimeError(
        "A_H_Flux not found in IS☉IS file."
    )

if energy_variable not in isois.cdf_info().zVariables:
    raise RuntimeError(
        "H_ENERGY not found in IS☉IS file."
    )


# ------------------------------------------------------------
# Read proton flux
# ------------------------------------------------------------

flux = np.asarray(
    isois.varget(
        flux_variable
    ),
    dtype=float
)

flux_attrs = isois.varattsget(
    flux_variable
)


# ------------------------------------------------------------
# Read proton energies
# ------------------------------------------------------------

energy = np.asarray(
    isois.varget(
        energy_variable
    ),
    dtype=float
)


# ------------------------------------------------------------
# Read IS☉IS timestamps
# ------------------------------------------------------------

isois_epoch_name = flux_attrs["DEPEND_0"]

isois_epoch = isois.varget(
    isois_epoch_name
)

isois_time = cdfepoch.to_datetime(
    isois_epoch
)


# ============================================================
# CLEAN FLUX DATA
# ============================================================

valid_flux = np.isfinite(flux)

fill_value = flux_attrs.get(
    "FILLVAL"
)

if fill_value is not None:

    fill_value = float(
        np.asarray(
            fill_value
        ).flatten()[0]
    )

    valid_flux &= ~np.isclose(
        flux,
        fill_value,
        rtol=0,
        atol=0
    )


# Keep zeros as valid measurements.
clean_flux = np.where(
    valid_flux,
    flux,
    np.nan
)


# ============================================================
# CLEAN ENERGY DATA
# ============================================================

energy_attrs = isois.varattsget(
    energy_variable
)

valid_energy = (
    np.isfinite(energy)
    & (energy > 0)
)

energy_fill = energy_attrs.get(
    "FILLVAL"
)

if energy_fill is not None:

    energy_fill = float(
        np.asarray(
            energy_fill
        ).flatten()[0]
    )

    valid_energy &= ~np.isclose(
        energy,
        energy_fill,
        rtol=0,
        atol=0
    )


energy = energy[
    valid_energy
]

clean_flux = clean_flux[
    :,
    valid_energy
]


# ============================================================
# SORT ENERGY CHANNELS
# ============================================================

order = np.argsort(
    energy
)

energy = energy[
    order
]

clean_flux = clean_flux[
    :,
    order
]


# ============================================================
# INFORMATION
# ============================================================

print("\nIS☉IS proton flux:")
print("Flux shape:", clean_flux.shape)
print("Number of times:", len(isois_time))
print("Number of energy channels:", len(energy))

print(
    "Energy range:",
    np.min(energy),
    "to",
    np.max(energy),
    "MeV"
)

print(
    "Flux units:",
    flux_attrs.get(
        "UNITS",
        "unknown"
    )
)


# ============================================================
# PREPARE FLUX FOR LOG COLOR SCALE
#
# Zero is scientifically valid,
# but log(0) does not exist.
#
# Therefore zeros are hidden ONLY for visualization.
# We are NOT treating them as missing measurements.
# ============================================================

plot_flux = np.ma.masked_where(
    (~np.isfinite(clean_flux))
    | (clean_flux <= 0),
    clean_flux
)

positive_flux = clean_flux[
    np.isfinite(clean_flux)
    & (clean_flux > 0)
]

if len(positive_flux) == 0:
    raise RuntimeError(
        "No positive proton flux values found."
    )

vmin = np.min(
    positive_flux
)

vmax = np.max(
    positive_flux
)

print(
    "Minimum positive flux:",
    vmin
)

print(
    "Maximum proton flux:",
    vmax
)


# ============================================================
# FIND TIME OF MAXIMUM FLUX
#
# Find maximum across all energy channels.
# ============================================================

max_index_flat = np.nanargmax(
    clean_flux
)

time_index, energy_index = np.unravel_index(
    max_index_flat,
    clean_flux.shape
)

peak_time = isois_time[
    time_index
]

peak_energy = energy[
    energy_index
]

peak_flux = clean_flux[
    time_index,
    energy_index
]


print("\nStrongest individual proton-flux bin:")
print("Time:", peak_time)
print("Energy:", peak_energy, "MeV")
print("Flux:", peak_flux)


# ============================================================
# PLOT
# ============================================================

fig, (ax1, ax2) = plt.subplots(
    2,
    1,
    figsize=(15, 10),
    sharex=True,
    gridspec_kw={
        "height_ratios": [1.2, 1]
    }
)


# ============================================================
# TOP PANEL — FIELDS
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
    "Parker Solar Probe — FIELDS + IS☉IS Proton Energy Spectrum\n"
    "2018-11-17"
)

ax1.legend(
    loc="upper right"
)

ax1.grid(
    True,
    alpha=0.3
)


# ============================================================
# BOTTOM PANEL — PROTON FLUX SPECTROGRAM
# ============================================================

mesh = ax2.pcolormesh(
    isois_time,
    energy,
    plot_flux.T,
    shading="auto",
    norm=LogNorm(
        vmin=vmin,
        vmax=vmax
    )
)

ax2.set_yscale(
    "log"
)

ax2.set_ylabel(
    "Proton energy [MeV]"
)

ax2.set_xlabel(
    "Time"
)


# ============================================================
# COLORBAR
# ============================================================

colorbar = fig.colorbar(
    mesh,
    ax=ax2
)

colorbar.set_label(
    "Differential proton flux"
)


# ============================================================
# MARK STRONGEST FLUX BIN
# ============================================================

ax1.axvline(
    peak_time,
    linestyle="--",
    alpha=0.7
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