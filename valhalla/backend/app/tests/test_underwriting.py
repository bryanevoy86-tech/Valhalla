from app.services.underwriting import compute_mao


def test_compute_mao_basic():
    # ARV 300k, repairs 50k, fee 10% -> MAO = 300k*0.7 - 50k - 30k = 130k
    assert compute_mao(300000, 50000, 0.10) == 130000.0


def test_compute_mao_floor_zero():
    assert compute_mao(100000, 120000, 0.10) == 0.0
