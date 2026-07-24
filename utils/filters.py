from config import DATA_ROLE_KEYWORDS


def is_data_role(text):

    if not text:

        return False

    text = text.lower()

    return any(

        keyword in text

        for keyword in DATA_ROLE_KEYWORDS

    )