from pathlib import Path
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
import shutil

from cdasws import CdasWs


# ============================================================
# LOCAL CACHE
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent

CACHE_DIR = (
    PROJECT_DIR
    / "data"
    / "cache"
)

CACHE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# NASA CDAWEB
# ============================================================

cdas = CdasWs()


# ============================================================
# DATASET IDS
#
# These are NASA CDAWeb dataset identifiers.
# ============================================================

PSP_FIELDS_RTN_1MIN = (
    "PSP_FLD_L2_MAG_RTN_1MIN"
)

PSP_ISOIS_LET1_HOURLY = (
    "PSP_ISOIS-EPIHI_L2-LET1-RATES3600"
)


# ============================================================
# DATE HANDLING
# ============================================================

def day_bounds(date_string):
    """
    Convert:

        2018-11-17

    into:

        2018-11-17T00:00:00Z
        2018-11-18T00:00:00Z
    """

    start = datetime.strptime(
        date_string,
        "%Y-%m-%d"
    )

    start = start.replace(
        tzinfo=timezone.utc
    )

    end = start + timedelta(
        days=1
    )

    start_string = (
        start.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    )

    end_string = (
        end.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    )

    return start_string, end_string


# ============================================================
# DOWNLOAD ONE NASA FILE
# ============================================================

def download_file(file_description):
    """
    Download one file returned by CDAWeb.

    If it already exists in the local cache,
    do not download it again.
    """

    url = file_description["Name"]

    length = int(
        file_description.get(
            "Length",
            0
        )
        or 0
    )

    filename = Path(
        urlparse(url).path
    ).name

    local_path = (
        CACHE_DIR
        / filename
    )


    # --------------------------------------------------------
    # CACHE HIT
    # --------------------------------------------------------

    if local_path.exists():

        print(
            "[CACHE HIT]",
            filename
        )

        return local_path


    # --------------------------------------------------------
    # CACHE MISS
    # --------------------------------------------------------

    print(
        "[CACHE MISS]",
        filename
    )

    print(
        "Downloading from NASA..."
    )

    temporary_file = cdas.download(
        url,
        length
    )

    if temporary_file is None:
        raise RuntimeError(
            "NASA download failed."
        )


    # Move NASA's temporary download
    # into our permanent local cache.

    shutil.move(
        temporary_file,
        local_path
    )


    print(
        "[SAVED]",
        local_path
    )

    return local_path


# ============================================================
# GENERIC NASA DATA REQUEST
# ============================================================

def get_nasa_files(
    dataset,
    start,
    end
):
    """
    Ask NASA which original CDF files cover
    the requested dataset and time interval.

    Files are downloaded only if they are not
    already present in the cache.
    """

    print()
    print(
        "NASA dataset:",
        dataset
    )

    print(
        "Time:",
        start,
        "to",
        end
    )


    status, files = (
        cdas.get_original_files(
            dataset,
            start,
            end
        )
    )


    if status != 200:
        raise RuntimeError(
            f"CDAWeb request failed. HTTP status: {status}"
        )


    if not files:
        raise RuntimeError(
            "NASA returned no files for this interval."
        )


    local_files = []

    for file_description in files:

        local_file = download_file(
            file_description
        )

        local_files.append(
            local_file
        )


    return local_files


# ============================================================
# GET ONE DAY
# ============================================================

def get_day_file(
    dataset,
    date_string
):
    """
    Retrieve the CDF belonging to one calendar day.
    """

    start, end = day_bounds(
        date_string
    )

    files = get_nasa_files(
        dataset,
        start,
        end
    )


    # Prefer a file whose filename contains
    # the requested YYYYMMDD date.

    date_token = date_string.replace(
        "-",
        ""
    )

    matching_files = [
        file
        for file in files
        if date_token in file.name
    ]


    if len(matching_files) == 1:

        return matching_files[0]


    if len(files) == 1:

        return files[0]


    raise RuntimeError(
        "More than one possible daily file was returned:\n"
        + "\n".join(
            str(file)
            for file in files
        )
    )


# ============================================================
# PARKER SOLAR PROBE CONVENIENCE FUNCTIONS
# ============================================================

def get_fields_1min(
    date_string
):
    """
    Parker Solar Probe FIELDS:
    1-minute RTN magnetic field.
    """

    return get_day_file(
        PSP_FIELDS_RTN_1MIN,
        date_string
    )


def get_isois_let1_hourly(
    date_string
):
    """
    Parker Solar Probe IS☉IS EPI-Hi LET1:
    hourly particle data.
    """

    return get_day_file(
        PSP_ISOIS_LET1_HOURLY,
        date_string
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    date = "2018-11-17"


    print()
    print(
        "=" * 70
    )

    print(
        "TESTING NASA DATA CACHE"
    )

    print(
        "=" * 70
    )


    fields_file = get_fields_1min(
        date
    )


    isois_file = get_isois_let1_hourly(
        date
    )


    print()
    print(
        "=" * 70
    )

    print(
        "FILES READY"
    )

    print(
        "=" * 70
    )

    print(
        "FIELDS:",
        fields_file
    )

    print(
        "IS☉IS :",
        isois_file
    )