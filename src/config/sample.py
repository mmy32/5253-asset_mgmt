"""Sample-definition rules for the active U.S. equity fund panel (paper, appendix A.1)."""

# CRSP objective codes kept: domestic equity, cap-based (EDC*) and growth/blend/income style.
# Excluded: EDS* (sector), EDYH (hedge, leveraged), EDYS (short), EF* (foreign), M, I, O.
# Inferred from the CRSP code scheme, not from the paper (which lists no codes); verify.
ACTIVE_US_EQUITY_OBJ_CODES = frozenset({"EDCL", "EDCM", "EDCS", "EDCI", "EDYG", "EDYB", "EDYI"})

# Paper: screen names to exclude international, balanced, sector, bond, money market, index funds.
EXCLUDED_NAME_PATTERN = r"international|balanced|sector|bond|money market|index"

# Paper: fund-months with a raw return above this value are removed.
MAX_RAW_RETURN = 1.0
