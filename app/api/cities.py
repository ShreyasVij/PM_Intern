"""
Cities API endpoints

Provides a simple endpoint to return the list of Indian city display names
backed by the generated backend.city_coords module.
"""
from __future__ import annotations

from flask import jsonify
import json
import os
import sys

try:
    from backend.city_coords import get_all_display_cities_sorted, CITY_COORDINATES  # type: ignore
except Exception:
    # Defensive fallback if module shape changes
    try:
        from backend.city_coords import CITY_COORDINATES  # type: ignore
    except Exception:
        CITY_COORDINATES = None  # type: ignore
    get_all_display_cities_sorted = None  # type: ignore


def list_cities():
    """Return sorted list of display city names.

    Response shape:
      { "cities": ["Mumbai", "Delhi", ...] }
    """
    try:
        # Attempt lazy import if globals are missing
        global get_all_display_cities_sorted, CITY_COORDINATES
        if get_all_display_cities_sorted is None or CITY_COORDINATES is None:
            try:
                import importlib
                mod = importlib.import_module('backend.city_coords')
                get_all_display_cities_sorted = getattr(mod, 'get_all_display_cities_sorted', None)
                CITY_COORDINATES = getattr(mod, 'CITY_COORDINATES', None)
            except Exception:
                # Try ensuring project root is on sys.path
                try:
                    # app/api -> app -> project root
                    proj = os.path.dirname(os.path.dirname(__file__))
                    proj = os.path.dirname(proj)
                    if proj not in sys.path:
                        sys.path.insert(0, proj)
                    import importlib as _il
                    mod = _il.import_module('backend.city_coords')
                    get_all_display_cities_sorted = getattr(mod, 'get_all_display_cities_sorted', None)
                    CITY_COORDINATES = getattr(mod, 'CITY_COORDINATES', None)
                except Exception:
                    pass

        # Preferred: use generated helper for display names
        if callable(get_all_display_cities_sorted):
            cities = get_all_display_cities_sorted()  # type: ignore
            if isinstance(cities, list) and cities:
                return jsonify({"cities": cities}), 200
        # Fallback: build names from CITY_COORDINATES keys
        if CITY_COORDINATES:
            def _titleize(name: str) -> str:
                # Keep hyphenated words like "pimpri-chinchwad" properly cased
                parts = []
                for token in name.split(' '):
                    if '-' in token:
                        sub = '-'.join(s[:1].upper() + s[1:] if s else s for s in token.split('-'))
                        parts.append(sub)
                    else:
                        parts.append(token[:1].upper() + token[1:] if token else token)
                return ' '.join(parts)
            display = sorted({_titleize(k) for k in CITY_COORDINATES.keys() if isinstance(k, str)})
            if display:
                return jsonify({"cities": display}), 200

        # Another fallback: read curated JSON file
        try:
            project_root = os.path.dirname(os.path.dirname(__file__))  # app/ -> project root is parent
            project_root = os.path.dirname(project_root)
            data_path = os.path.join(project_root, 'data', 'cities.in.json')
            with open(data_path, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            def _titleize(n: str) -> str:
                parts = []
                for token in n.split(' '):
                    if '-' in token:
                        parts.append('-'.join(s[:1].upper() + s[1:] if s else s for s in token.split('-')))
                    else:
                        parts.append(token[:1].upper() + token[1:] if token else token)
                return ' '.join(parts)
            display = sorted({_titleize((item.get('city') or '').strip().lower()) for item in raw if isinstance(item, dict) and item.get('city')})
            if display:
                return jsonify({"cities": display}), 200
        except Exception:
            pass
        # Last resort: minimal curated set so UI isn't empty in dev
        fallback = sorted([
            'Mumbai', 'Delhi', 'Bengaluru', 'Chennai', 'Kolkata', 'Pune', 'Jaipur', 'Chandigarh', 'Ahmedabad', 'Hyderabad'
        ])
        return jsonify({"cities": fallback}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
