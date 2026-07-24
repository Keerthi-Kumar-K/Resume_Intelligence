import re

import string

from rapidfuzz import fuzz


def normalize(text):

    text = text.lower()

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def remove_punctuation(text):

    return text.translate(

        str.maketrans(

            "",

            "",

            string.punctuation

        )

    )


def fuzzy_score(a,b):

    return fuzz.token_sort_ratio(a,b)