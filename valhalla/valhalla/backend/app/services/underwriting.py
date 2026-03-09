def compute_mao(arv: float, repairs: float, fee: float = 0.10) -> float:
    """
    Wholesale MAO rule-of-thumb:
      MAO = (ARV * 0.70) - repairs - (ARV * fee)
    - 'fee' can represent assignment fee, holding, closing, etc.
    """
    arv = float(arv or 0.0)
    repairs = float(repairs or 0.0)
    fee_val = arv * float(fee or 0.0)
    mao = (arv * 0.70) - repairs - fee_val
    return max(0.0, round(mao, 2))
