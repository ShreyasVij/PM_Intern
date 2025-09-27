"""
Admin/diagnostics endpoints

Provides small runtime checks like DB collection counts to verify
MongoDB Atlas-only mode is working and data is present.
"""

from flask import jsonify
from app.core.database import db_manager
from app.utils.logger import app_logger
from app.utils.response_helpers import success_response, error_response

import os
from app.config import get_config


def db_stats():
    """Return basic counts for key collections in MongoDB.

    Response shape:
      {
        "database": "connected" | "disconnected",
        "atlas_only": true|false,
        "counts": {
          "profiles": 0,
          "internships": 0,
          "login_info": 0,
          "skills_synonyms": 0
        }
      }
    """
    try:
        # Read atlas-only flag at request time
        try:
            _cfg = get_config()
            atlas_only = bool(getattr(_cfg, 'DISABLE_JSON_FALLBACK', False))
        except Exception:
            atlas_only = os.getenv('DISABLE_JSON_FALLBACK', 'False').lower() == 'true'

        db = db_manager.get_db()
        if db is None:
            return success_response({
                "database": "disconnected",
                "atlas_only": atlas_only,
                "counts": {
                    "profiles": 0,
                    "internships": 0,
                    "login_info": 0,
                    "skills_synonyms": 0
                }
            })

        def _count(name: str) -> int:
            try:
                return db[name].count_documents({})
            except Exception as e:
                app_logger.warning(f"Count failed for {name}: {e}")
                return 0

        counts = {
            "profiles": _count("profiles"),
            "internships": _count("internships"),
            "login_info": _count("login_info"),
            "skills_synonyms": _count("skills_synonyms"),
        }

        return success_response({
            "database": "connected",
            "atlas_only": atlas_only,
            "counts": counts
        })
    except Exception as e:
        app_logger.error(f"/api/admin/db-stats error: {e}")
        return error_response("Failed to fetch DB stats", 500)
