#!/usr/bin/env python3
import math

from backend.distance_matrix import get_distance, normalize_city_name
from backend.city_coords import CITY_COORDINATES


def test_known_city_coords_present():
    # spot check a few cities
    for key in ["mumbai", "pune", "delhi", "jaipur"]:
        assert key in CITY_COORDINATES


def test_distance_sanity_mumbai_pune():
    d = get_distance("Mumbai", "Pune")
    # Real-world road distance ~150km; aerial ~120-150 km; allow tolerance
    assert 90 <= d <= 170


def test_distance_sanity_delhi_jaipur():
    d = get_distance("Delhi", "Jaipur")
    assert 200 <= d <= 320


def test_normalization_aliases():
    assert normalize_city_name("Bombay") in ("mumbai",)