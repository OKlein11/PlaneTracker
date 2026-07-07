import pytest

from flaskapp.convert import icao_to_n, n_to_icao


@pytest.mark.parametrize("nnumber", ["N1", "N1A", "N12345", "N123AB", "N999ZZ"])
def test_round_trip_n_to_icao_to_n(nnumber):
    icao = n_to_icao(nnumber)
    assert icao is not None
    assert icao_to_n(icao) == nnumber


def test_icao_to_n_known_value():
    assert icao_to_n("a1b2c3") == "N2085A"


def test_n_to_icao_known_value():
    assert n_to_icao("N1") == "a00001"
