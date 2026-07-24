import pdfplumber

from docx import Document

from pathlib import Path


class Parser:

    @staticmethod
    def read_pdf(path):

        text = ""

        with pdfplumber.open(path) as pdf:

            for page in pdf.pages:

                t = page.extract_text()

                if t:

                    text += t + "\n"

        return text


    @staticmethod
    def read_docx(path):

        doc = Document(path)

        return "\n".join(

            p.text

            for p in doc.paragraphs

        )


    @staticmethod
    def read(path):

        path = Path(path)

        suffix = path.suffix.lower()

        if suffix == ".pdf":

            return Parser.read_pdf(path)

        if suffix == ".docx":

            return Parser.read_docx(path)

        raise ValueError(f"Unsupported file: {suffix}")