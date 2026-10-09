import numpy as np
import matplotlib.pyplot as plt

from scipy.signal import find_peaks
from scipy.optimize import curve_fit


# ============================================================
# 1. Gaussian detector response
# ============================================================

def gaussian(t, baseline, amplitude, t0, sigma):

    return (
        baseline
        + amplitude
        * np.exp(
            -((t - t0) ** 2)
            / (2 * sigma ** 2)
        )
    )


# ============================================================
# 2. General simulation settings
# ============================================================

rng = np.random.default_rng(42)

sampling_rate = 10_000       # samples / second
duration = 0.040             # 40 ms

time = np.arange(
    0,
    duration,
    1 / sampling_rate
)


# Detector properties
noise_sigma = 0.08           # V
true_pulse_sigma = 0.002     # 2 ms


# Detection threshold
threshold_sigma = 5


# Number of simulated particles PER SNR value
events_per_snr = 1000


# SNR values we want to study
snr_values = np.array([
    1,
    2,
    3,
    4,
    5,
    6,
    8,
    10,
    15,
    20
])


# ============================================================
# 3. Result storage
# ============================================================

efficiencies = []

timing_resolutions = []
amplitude_resolutions = []

timing_biases = []
amplitude_biases = []

false_positive_rates = []


# ============================================================
# 4. Scan over SNR
# ============================================================

for snr in snr_values:

    # --------------------------------------------------------
    # Fix the TRUE amplitude for this SNR
    #
    # SNR = amplitude / noise_sigma
    #
    # therefore:
    #
    # amplitude = SNR * noise_sigma
    # --------------------------------------------------------

    true_amplitude = (
        snr * noise_sigma
    )


    correct_detections = 0
    false_positives = 0

    timing_errors = []
    amplitude_errors = []


    # ========================================================
    # Run many particles at THIS SNR
    # ========================================================

    for experiment in range(events_per_snr):

        # ----------------------------------------------------
        # Random true arrival time
        # ----------------------------------------------------

        true_time = rng.uniform(
            0.018,
            0.022
        )


        # ----------------------------------------------------
        # Ideal particle pulse
        # ----------------------------------------------------

        clean_signal = gaussian(
            time,
            0.0,
            true_amplitude,
            true_time,
            true_pulse_sigma
        )


        # ----------------------------------------------------
        # Add electronic noise
        # ----------------------------------------------------

        noise = rng.normal(
            0.0,
            noise_sigma,
            size=len(time)
        )

        signal = (
            clean_signal
            + noise
        )


        # ----------------------------------------------------
        # Measure baseline + noise
        #
        # Particle is around 18-22 ms,
        # so first 10 ms contain only noise.
        # ----------------------------------------------------

        noise_region = signal[
            time < 0.010
        ]

        measured_baseline = np.mean(
            noise_region
        )

        measured_noise_sigma = np.std(
            noise_region,
            ddof=1
        )


        # ----------------------------------------------------
        # Detection threshold
        # ----------------------------------------------------

        threshold = (
            measured_baseline
            + threshold_sigma
            * measured_noise_sigma
        )


        # ----------------------------------------------------
        # Peak detection
        # ----------------------------------------------------

        peaks, properties = find_peaks(
            signal,
            height=threshold,
            distance=int(
                0.005 * sampling_rate
            )
        )


        # ----------------------------------------------------
        # Is there a detected peak close to the true particle?
        # ----------------------------------------------------

        if len(peaks) == 0:
            continue


        peak_times = time[peaks]

        time_differences = np.abs(
            peak_times - true_time
        )


        # We consider a peak correctly associated with
        # the particle if it is within 1 ms.
        matching_window = 0.001


        matched_mask = (
            time_differences
            <= matching_window
        )


        matched_peaks = peaks[
            matched_mask
        ]


        # Peaks elsewhere are noise detections
        false_positives += np.sum(
            ~matched_mask
        )


        if len(matched_peaks) == 0:
            continue


        # Particle successfully detected
        correct_detections += 1


        # If more than one candidate is near the particle,
        # choose the strongest
        matched_peak = matched_peaks[
            np.argmax(
                signal[matched_peaks]
            )
        ]


        detected_time = time[
            matched_peak
        ]


        # ====================================================
        # 5. Gaussian reconstruction
        # ====================================================

        fit_window = 0.006


        fit_mask = (
            (time >= detected_time - fit_window)
            &
            (time <= detected_time + fit_window)
        )


        fit_time = time[
            fit_mask
        ]

        fit_signal = signal[
            fit_mask
        ]


        baseline_guess = measured_baseline

        amplitude_guess = (
            signal[matched_peak]
            - measured_baseline
        )


        try:

            parameters, covariance = curve_fit(

                gaussian,

                fit_time,
                fit_signal,

                p0=[
                    baseline_guess,
                    amplitude_guess,
                    detected_time,
                    true_pulse_sigma
                ],

                bounds=(

                    [
                        -0.5,
                        0.0,
                        detected_time - 0.003,
                        0.0005
                    ],

                    [
                        0.5,
                        3.0,
                        detected_time + 0.003,
                        0.006
                    ]
                ),

                maxfev=10000
            )


        except (RuntimeError, ValueError):
            continue


        fitted_baseline = parameters[0]
        fitted_amplitude = parameters[1]
        fitted_time = parameters[2]
        fitted_sigma = parameters[3]


        # ====================================================
        # 6. Reconstruction errors
        # ====================================================

        timing_error_us = (
            fitted_time
            - true_time
        ) * 1_000_000


        amplitude_error_percent = (
            (
                fitted_amplitude
                - true_amplitude
            )
            / true_amplitude
            * 100
        )


        timing_errors.append(
            timing_error_us
        )

        amplitude_errors.append(
            amplitude_error_percent
        )


    # ========================================================
    # 7. Results for THIS SNR
    # ========================================================

    efficiency = (
        correct_detections
        / events_per_snr
        * 100
    )


    false_positive_rate = (
        false_positives
        / events_per_snr
    )


    efficiencies.append(
        efficiency
    )

    false_positive_rates.append(
        false_positive_rate
    )


    # Reconstruction statistics only make sense if
    # enough particles were reconstructed
    if len(timing_errors) > 1:

        timing_errors = np.array(
            timing_errors
        )

        amplitude_errors = np.array(
            amplitude_errors
        )


        timing_bias = np.mean(
            timing_errors
        )

        timing_resolution = np.std(
            timing_errors,
            ddof=1
        )


        amplitude_bias = np.mean(
            amplitude_errors
        )

        amplitude_resolution = np.std(
            amplitude_errors,
            ddof=1
        )


    else:

        timing_bias = np.nan
        timing_resolution = np.nan

        amplitude_bias = np.nan
        amplitude_resolution = np.nan


    timing_biases.append(
        timing_bias
    )

    timing_resolutions.append(
        timing_resolution
    )

    amplitude_biases.append(
        amplitude_bias
    )

    amplitude_resolutions.append(
        amplitude_resolution
    )


    # --------------------------------------------------------
    # Print result for this SNR
    # --------------------------------------------------------

    print("\n--------------------------------------")

    print(
        f"SNR = {snr}"
    )

    print(
        f"True amplitude = "
        f"{true_amplitude:.3f} V"
    )

    print(
        f"Detection efficiency = "
        f"{efficiency:.1f}%"
    )

    print(
        f"False positives / waveform = "
        f"{false_positive_rate:.3f}"
    )


    if not np.isnan(timing_resolution):

        print(
            f"Timing resolution = "
            f"{timing_resolution:.2f} us"
        )

        print(
            f"Timing bias = "
            f"{timing_bias:.2f} us"
        )

        print(
            f"Amplitude resolution = "
            f"{amplitude_resolution:.2f}%"
        )

        print(
            f"Amplitude bias = "
            f"{amplitude_bias:.2f}%"
        )


# ============================================================
# 8. Convert results
# ============================================================

efficiencies = np.array(
    efficiencies
)

timing_resolutions = np.array(
    timing_resolutions
)

amplitude_resolutions = np.array(
    amplitude_resolutions
)

timing_biases = np.array(
    timing_biases
)

amplitude_biases = np.array(
    amplitude_biases
)


# ============================================================
# 9. GRAPH 1
#    Detection Efficiency vs SNR
# ============================================================

plt.figure(
    figsize=(9, 6)
)

plt.plot(
    snr_values,
    efficiencies,
    marker="o"
)

plt.axhline(
    95,
    linestyle="--",
    label="95% efficiency"
)

plt.xlabel(
    "True SNR"
)

plt.ylabel(
    "Detection Efficiency [%]"
)

plt.title(
    "Particle Detection Efficiency vs SNR"
)

plt.ylim(
    -5,
    105
)

plt.grid(
    alpha=0.3
)

plt.legend()

plt.tight_layout()


# ============================================================
# 10. GRAPH 2
#     Timing Resolution vs SNR
# ============================================================

plt.figure(
    figsize=(9, 6)
)

plt.plot(
    snr_values,
    timing_resolutions,
    marker="o"
)

plt.xlabel(
    "True SNR"
)

plt.ylabel(
    "Timing Resolution σ(Δt) [microseconds]"
)

plt.title(
    "Timing Resolution vs SNR"
)

plt.grid(
    alpha=0.3
)

plt.tight_layout()


# ============================================================
# 11. GRAPH 3
#     Amplitude Resolution vs SNR
# ============================================================

plt.figure(
    figsize=(9, 6)
)

plt.plot(
    snr_values,
    amplitude_resolutions,
    marker="o"
)

plt.xlabel(
    "True SNR"
)

plt.ylabel(
    "Amplitude Resolution σ(ΔA/A) [%]"
)

plt.title(
    "Amplitude Resolution vs SNR"
)

plt.grid(
    alpha=0.3
)

plt.tight_layout()


# ============================================================
# Show figures
# ============================================================

plt.show()