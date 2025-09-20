"""
City endpoints: list known cities and validate/persist free-typed cities via distance_matrix.
"""
from flask import jsonify, request
import re
import os

try:
    from backend.distance_matrix import CITY_COORDINATES, get_coordinates, normalize_city_name
except Exception:
    # Fallbacks if backend module pathing differs
    CITY_COORDINATES = {}
    def get_coordinates(city: str):
        return None
    def normalize_city_name(city: str) -> str:
        return (city or "").strip().lower()


def _display_name(key: str) -> str:
    if not isinstance(key, str):
        return ""
    parts = []
    for chunk in key.split(" "):
        parts.append("-".join(p.capitalize() for p in chunk.split("-")))
    return " ".join(parts)


def list_cities():
    try:
        keys = list((CITY_COORDINATES or {}).keys())
    except Exception:
        keys = []
    cities = sorted([_display_name(k) for k in keys if k], key=lambda s: s.lower())
    return jsonify({"cities": cities}), 200


def validate_city():
    data = request.get_json(silent=True) or {}
    raw_city = (data.get("city") or "").strip()
    if not raw_city:
        return jsonify({"ok": False, "error": "city is required"}), 400
    # Basic input sanity: at least 3 letters and contains alphabets
    if len(raw_city) < 3 or not re.search(r"[A-Za-z]", raw_city):
        return jsonify({"ok": False, "error": "enter a valid city name"}), 400

    coords = get_coordinates(raw_city)
    if not coords:
        norm = normalize_city_name(raw_city)
        coords = get_coordinates(norm)
    if not coords:
        return jsonify({"ok": False, "error": "city not found"}), 404

    norm_key = normalize_city_name(raw_city)
    # Additional strictness: for new cities not already known, disallow very short ambiguous names
    allow_short = {"leh"}  # whitelist of legitimate short city names
    if len(norm_key) < 4 and norm_key not in allow_short and norm_key not in (CITY_COORDINATES or {}):
        return jsonify({"ok": False, "error": "city name too short or ambiguous; please enter full city name"}), 400
    return jsonify({
        "ok": True,
        "normalized": norm_key,
        "display": _display_name(norm_key),
        "lat": coords[0],
        "lon": coords[1]
    }), 200
