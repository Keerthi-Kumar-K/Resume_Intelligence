"""Single authoritative final-score calculation."""
from __future__ import annotations


class FinalRanker:
    WEIGHTS_PLATFORM = {
        "platform": 0.30, "required": 0.22, "role": 0.15, "experience": 0.13,
        "preferred": 0.04, "achievement": 0.05, "complexity": 0.05,
        "semantic": 0.025, "bm25": 0.025, "domain": 0.005, "certification": 0.005,
    }
    WEIGHTS_GENERIC = {
        "required": 0.30, "role": 0.23, "experience": 0.16, "preferred": 0.08,
        "achievement": 0.06, "complexity": 0.05, "semantic": 0.045,
        "bm25": 0.045, "domain": 0.015, "certification": 0.015,
    }

    def calculate(self, scores, weights=None, hard_gate_cap=100.0, has_target_platform=True):
        w = self.WEIGHTS_PLATFORM if has_target_platform else self.WEIGHTS_GENERIC
        values = {
            "platform": scores.platform_score, "required": scores.required_skill_score,
            "role": scores.role_score, "experience": scores.experience_score,
            "preferred": scores.preferred_skill_score, "achievement": scores.achievement_score,
            "complexity": scores.complexity_score, "semantic": scores.semantic_score,
            "bm25": scores.bm25_score, "domain": scores.domain_score,
            "certification": scores.certification_score,
        }
        weighted = sum(values[key] * weight for key, weight in w.items())

        penalty = (
            scores.missing_required_penalty * 0.20
            + scores.role_mismatch_penalty * 0.35
            + scores.experience_penalty * 0.25
            + scores.platform_mismatch_penalty
            + scores.critical_skill_penalty
        )
        if has_target_platform and scores.platform_score < 80:
            penalty += (80.0 - scores.platform_score) * 0.22
        if scores.required_skill_score < 55:
            penalty += (55.0 - scores.required_skill_score) * 0.10

        bonus = 0.0
        if has_target_platform and scores.platform_score >= 72 and scores.required_skill_score >= 80 and scores.role_score >= 90:
            bonus = 8.0
            if scores.platform_score >= 86 and scores.experience_score >= 70:
                bonus = 10.0
        elif (not has_target_platform) and scores.required_skill_score >= 82 and scores.role_score >= 85:
            bonus = 4.0

        # Core evidence acts as a gentle gate, preventing generic strengths from fully compensating.
        if has_target_platform:
            core_floor = min(scores.platform_score, scores.required_skill_score, scores.role_score)
            gate_factor = 0.90 + 0.10 * max(0.0, min(1.0, core_floor / 100.0))
        else:
            core_floor = min(scores.required_skill_score, scores.role_score)
            gate_factor = 0.93 + 0.07 * max(0.0, min(1.0, core_floor / 100.0))

        final = (weighted + bonus - penalty) * gate_factor
        final = min(float(hard_gate_cap or 100.0), final)
        return round(weighted, 2), round(penalty, 2), round(max(0.0, min(100.0, final)), 2)
