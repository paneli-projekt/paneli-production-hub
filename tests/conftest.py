# -*- coding: utf-8 -*-
"""Zajedničko za sve testove. D-75: ponuda i izvoz na pilu traže POTVRĐENO slaganje; postojeći testovi (korak 2–5) rade s automatskom
potvrdom Hubovog prijedloga (kao CLI --potvrdi-opt), a pravilo samo se testira u tests/test_optimizacija_potvrda.py uz AUTO_POTVRDA = False."""
import pytest

from hub.nalozi import optimiziraj as OP


@pytest.fixture(autouse=True)
def _auto_potvrda_optimizacije():
    staro = OP.AUTO_POTVRDA
    OP.AUTO_POTVRDA = True
    yield
    OP.AUTO_POTVRDA = staro
