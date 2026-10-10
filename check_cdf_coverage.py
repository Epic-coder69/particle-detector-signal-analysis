from pathlib import Path

import numpy as np
from cdflib import CDF, cdfepoch


# ============================================================
# SETTINGS
# ============================================================

folder = Path(".")

cdf_files = sorted(folder.glob("*.cdf"))

if not cdf_files:
    raise RuntimeError("No .cdf files found in the current folder.")


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_valid_mask(data, attributes):
    """
    Determine which numeric values are actually present.

    IMPORTANT:
    Zero is considered VALID.

    We remove:
    - NaN / infinity
    - the CDF FILLVAL used to represent missing data
    """

    data = np.asarray(data)

    valid = np.isfinite(data)

    fill_value = attributes.get("FILLVAL")

    if fill_value is not None:
        fill_values = np.asarray(fill_value).flatten()

        for fill in fill_values:
            try:
                fill = float(fill)

                valid &= ~np.isclose(
                    data,
                    fill,
                    rtol=0,
                    atol=0
                )

            except (ValueError, TypeError):
                pass

    return valid


def get_time_information(cdf, attributes, data):
    """
    Find the time variable attached to a science variable.

    Returns:
        epoch_name
        number of timestamps
        approximate cadence in seconds
        first time
        last time
    """

    epoch_name = attributes.get("DEPEND_0")

    if epoch_name is None:
        return None, None, None, None, None

    try:
        epoch = cdf.varget(epoch_name)
        times = cdfepoch.to_datetime(epoch)

    except Exception:
        return epoch_name, None, None, None, None

    if len(times) == 0:
        return epoch_name, 0, None, None, None

    first_time = times[0]
    last_time = times[-1]

    cadence_seconds = None

    if len(times) > 1:
        times_ns = times.astype("datetime64[ns]").astype(np.int64)

        differences = np.diff(times_ns) / 1e9

        differences = differences[
            np.isfinite(differences)
            & (differences > 0)
        ]

        if len(differences) > 0:
            cadence_seconds = np.median(differences)

    return (
        epoch_name,
        len(times),
        cadence_seconds,
        first_time,
        last_time
    )


def format_cadence(seconds):
    if seconds is None:
        return "unknown"

    if seconds < 60:
        return f"{seconds:.1f} s"

    if seconds < 3600:
        return f"{seconds / 60:.2f} min"

    return f"{seconds / 3600:.2f} hr"


# ============================================================
# SCAN FILES
# ============================================================

print("\n")
print("=" * 90)
print("PARKER SOLAR PROBE CDF COVERAGE CHECK")
print("=" * 90)


for filename in cdf_files:

    print("\n\n")
    print("#" * 90)
    print("FILE:")
    print(filename.name)
    print("#" * 90)

    try:
        cdf = CDF(str(filename))

    except Exception as error:
        print("Could not open file:")
        print(error)
        continue

    info = cdf.cdf_info()

    science_variables = []


    # ========================================================
    # FIND SCIENCE DATA VARIABLES
    # ========================================================

    for variable in info.zVariables:

        try:
            attributes = cdf.varattsget(variable)

        except Exception:
            continue

        var_type = str(
            attributes.get("VAR_TYPE", "")
        ).lower()

        # Ignore metadata/support variables
        if var_type != "data":
            continue

        try:
            data = np.asarray(
                cdf.varget(variable)
            )

        except Exception:
            continue

        # Ignore strings and non-numeric arrays
        if not np.issubdtype(
            data.dtype,
            np.number
        ):
            continue

        # Ignore empty variables
        if data.size == 0:
            continue


        # ====================================================
        # VALID DATA CHECK
        # ====================================================

        data_float = data.astype(float)

        valid = get_valid_mask(
            data_float,
            attributes
        )

        total_cells = data_float.size
        valid_cells = np.sum(valid)

        valid_fraction = (
            100 * valid_cells / total_cells
        )


        # ====================================================
        # NON-ZERO INFORMATION
        # ====================================================

        if valid_cells > 0:

            nonzero_cells = np.sum(
                valid & (data_float != 0)
            )

            nonzero_fraction = (
                100 * nonzero_cells / valid_cells
            )

        else:
            nonzero_cells = 0
            nonzero_fraction = 0


        # ====================================================
        # TIME COVERAGE
        # ====================================================

        (
            epoch_name,
            number_times,
            cadence,
            first_time,
            last_time

        ) = get_time_information(
            cdf,
            attributes,
            data_float
        )


        # How many timestamps contain at least one
        # VALID measurement?
        time_coverage = None
        valid_times = None

        if (
            number_times is not None
            and data_float.ndim >= 1
            and data_float.shape[0] == number_times
        ):

            valid_by_time = valid.reshape(
                valid.shape[0],
                -1
            ).any(axis=1)

            valid_times = np.sum(
                valid_by_time
            )

            time_coverage = (
                100
                * valid_times
                / number_times
            )


        # ====================================================
        # DESCRIPTION
        # ====================================================

        description = attributes.get(
            "CATDESC",
            attributes.get(
                "FIELDNAM",
                ""
            )
        )

        units = attributes.get(
            "UNITS",
            ""
        )


        science_variables.append(
            {
                "name": variable,
                "shape": data_float.shape,
                "description": description,
                "units": units,
                "valid_fraction": valid_fraction,
                "nonzero_fraction": nonzero_fraction,
                "valid_cells": valid_cells,
                "total_cells": total_cells,
                "valid_times": valid_times,
                "number_times": number_times,
                "time_coverage": time_coverage,
                "cadence": cadence,
                "epoch": epoch_name,
                "first_time": first_time,
                "last_time": last_time,
            }
        )


    # ========================================================
    # PRINT FILE SUMMARY
    # ========================================================

    if not science_variables:

        print("\nNo numeric science-data variables found.")
        continue


    # Prefer variables with many timestamps and good coverage
    science_variables.sort(
        key=lambda x: (
            x["time_coverage"]
            if x["time_coverage"] is not None
            else -1,

            x["number_times"]
            if x["number_times"] is not None
            else -1
        ),
        reverse=True
    )


    print(
        f"\nFound {len(science_variables)} "
        "numeric science variables."
    )

    print(
        "\nShowing the 12 strongest candidates:"
    )


    # ========================================================
    # SHOW TOP VARIABLES
    # ========================================================

    for variable in science_variables[:12]:

        print("\n" + "-" * 75)

        print(
            "Variable:",
            variable["name"]
        )

        print(
            "Description:",
            variable["description"]
        )

        print(
            "Units:",
            variable["units"]
        )

        print(
            "Shape:",
            variable["shape"]
        )

        print(
            "Valid numeric cells:",
            f'{variable["valid_fraction"]:.2f}%'
        )

        print(
            "Non-zero among valid cells:",
            f'{variable["nonzero_fraction"]:.2f}%'
        )


        if variable["number_times"] is not None:

            print(
                "Time records:",
                variable["number_times"]
            )


        if variable["time_coverage"] is not None:

            print(
                "Valid timestamp coverage:",
                f'{variable["time_coverage"]:.2f}%'
            )


        print(
            "Approximate cadence:",
            format_cadence(
                variable["cadence"]
            )
        )


        if variable["first_time"] is not None:

            print(
                "First timestamp:",
                variable["first_time"]
            )

            print(
                "Last timestamp:",
                variable["last_time"]
            )


print("\n")
print("=" * 90)
print("DONE")
print("=" * 90)