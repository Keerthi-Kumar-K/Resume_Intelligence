from datetime import datetime

from pathlib import Path

from config import LOG_ROOT


class Logger:

    def __init__(self, portal):

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.file = LOG_ROOT / f"{portal}_{stamp}.log"

    def write(self, text):

        print(text)

        with open(

            self.file,

            "a",

            encoding="utf-8"

        ) as f:

            f.write(text + "\n")