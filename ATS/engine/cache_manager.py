import pickle
from pathlib import Path


class CacheManager:

    @staticmethod
    def load(path):

        path = Path(path)

        if path.exists():

            with open(path, "rb") as f:

                return pickle.load(f)

        return {}


    @staticmethod
    def save(data, path):

        path = Path(path)

        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "wb") as f:

            pickle.dump(data, f)