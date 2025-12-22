"""DSR/PSR Skill Calculator (Domain Service)"""

import math

from libs.shared.src.enums.skill_level import SkillLevel


class SkillMetricsCalculator:
    """
    DSR/PSR Skill Calculator

    Pure business logic, no I/O dependencies

    | DSR       | Assessment     | Action             |
    | --------- | -------------- | ------------------ |
    | > 0.95    | Skill dominant | Increase allocation |
    | 0.75-0.95 | Possible skill | Maintain allocation |
    | 0.50-0.75 | Indeterminate  | Reduce allocation   |
    | < 0.50    | Luck dominant  | Consider disabling  |
    """

    def calculate_dsr(self, sharpe: float, num_trials: int) -> float:
        """
        Calculate Deflated Sharpe Ratio

        Args:
            sharpe: Sharpe Ratio
            num_trials: Number of trials

        Returns:
            float: DSR value
        """
        if num_trials <= 1:
            return 0.0

        # DSR = SR / sqrt(1 + 0.5 * ln(num_trials))
        adjustment = math.sqrt(1 + 0.5 * math.log(num_trials))
        return sharpe / adjustment

    def calculate_psr(self, sharpe: float, benchmark_sharpe: float, n: int) -> float:
        """
        Calculate Probabilistic Sharpe Ratio

        Args:
            sharpe: Sharpe Ratio
            benchmark_sharpe: Benchmark Sharpe
            n: Number of observations

        Returns:
            float: PSR value (0-1)
        """
        if n <= 1:
            return 0.5

        # Simplified PSR calculation
        se = 1 / math.sqrt(n)
        z = (sharpe - benchmark_sharpe) / se

        # Approximate normal CDF
        psr = 0.5 * (1 + math.erf(z / math.sqrt(2)))
        return max(0, min(1, psr))

    def classify_skill(self, dsr: float) -> SkillLevel:
        """
        Classify skill level

        Args:
            dsr: DSR value

        Returns:
            SkillLevel: Skill level
        """
        if dsr > 0.95:
            return SkillLevel.SKILL_DOMINATED
        elif dsr > 0.75:
            return SkillLevel.POSSIBLE_SKILL
        elif dsr > 0.50:
            return SkillLevel.INDETERMINATE
        else:
            return SkillLevel.LUCK_DOMINATED
