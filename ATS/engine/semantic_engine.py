from dataclasses import dataclass
from typing import Optional

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from ATS.config.scoring_config import MODEL_PATH


@dataclass
class SemanticResult:

    score: float = 0.0

    cosine_similarity: float = 0.0


class SemanticEngine:

    _model: Optional[SentenceTransformer] = None

    def __init__(self):

        if SemanticEngine._model is None:

            SemanticEngine._model = SentenceTransformer(
                str(MODEL_PATH)
            )

        self.model = SemanticEngine._model

    def compare(
        self,
        resume_text: str,
        jd_text: str,
    ) -> SemanticResult:

        resume_text = str(resume_text or "").strip()

        jd_text = str(jd_text or "").strip()

        if not resume_text or not jd_text:

            return SemanticResult()

        embeddings = self.model.encode(
            [resume_text, jd_text],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        similarity = float(
            cosine_similarity(
                [embeddings[0]],
                [embeddings[1]],
            )[0][0]
        )

        similarity = max(
            0.0,
            min(1.0, similarity),
        )

        return SemanticResult(
            score=round(similarity * 100, 2),
            cosine_similarity=round(similarity, 4),
        )

    def embed(self, text: str):

        return self.model.encode(
            str(text or ""),
            convert_to_numpy=True,
            normalize_embeddings=True,
        )