from pathlib import Path

from datetime import datetime

from config import OUTPUT_ROOT


def create_output_folder(portal):

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    folder = OUTPUT_ROOT / f"{portal}_{stamp}"

    folder.mkdir(parents=True, exist_ok=True)

    return folder