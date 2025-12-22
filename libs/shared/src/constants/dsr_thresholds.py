"""DSR Skill Judgment Thresholds

Corresponds to methodology.md §2 Investment Philosophy and Metacognition
"""

# DSR (Deflated Sharpe Ratio) judgment thresholds
DSR_SKILL = 0.95  # Valid strategy: DSR ≥ 0.95
DSR_GRAY_ZONE = 0.80  # Gray zone lower bound: 0.80 ≤ DSR < 0.95
DSR_LUCK = 0.80  # False positive upper bound: DSR < 0.80 should be discarded

# Legacy compatibility (deprecated)
DSR_POSSIBLE_SKILL = 0.80
