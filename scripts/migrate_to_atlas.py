"""
One-time migration utility to seed MongoDB Atlas from local JSON files.

- Reads data from data/*.json
- Connects to MongoDB using MONGO_URI and DB_NAME from environment/.env
- Creates basic indexes
- Upserts documents keyed by stable IDs (candidate_id, internship_id, username)
- Prints a concise summary at the end

Usage (Windows cmd):
    set PYTHONPATH=.
    python scripts\migrate_to_atlas.py

Ensure your .env contains a valid Atlas connection string, e.g.:
    MONGO_URI=mongodb+srv://<user>:<pass>@<cluster>/<db>?retryWrites=true&w=majority&appName=<app>
    DB_NAME=internship_recommender
"""
from __future__ import annotations
import os
import json
from typing import Any, Dict, List
from pymongo import MongoClient, UpdateOne
from pymongo.errors import PyMongoError
from bson import ObjectId
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, 'data')


def load_json(name: str) -> List[Dict[str, Any]]:
    fp = os.path.join(DATA_DIR, f'{name}.json')
    if not os.path.exists(fp):
        print(f"[warn] data file not found: {fp}")
        return []
    with open(fp, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                # Some files might wrap results
                for k in ('profiles','internships','users','login_info','login-info','data'):
                    v = data.get(k)
                    if isinstance(v, list):
                        return v
            return []
        except Exception as e:
            print(f"[error] failed parsing {fp}: {e}")
            return []


def to_object_id(val: Any) -> Any:
    if isinstance(val, str):
        try:
            return ObjectId(val)
        except Exception:
            return val
    return val


def main():
    load_dotenv(os.path.join(ROOT, '.env'))
    mongo_uri = os.getenv('MONGO_URI')
    db_name = os.getenv('DB_NAME', 'internship_recommender')
    if not mongo_uri or not mongo_uri.startswith('mongodb'):
        print('[fatal] MONGO_URI missing or invalid. Configure your Atlas connection string in .env')
        return 1

    client = MongoClient(mongo_uri)
    db = client[db_name]

    # Collections to migrate: profiles, internships, login_info (or login-info), skills_synonyms
    profiles = load_json('profiles')
    internships = load_json('internships')
    login_info = load_json('login_info') or load_json('login-info')
    skills_synonyms = load_json('skills_synonyms')

    # Prepare bulk ops
    prof_ops: List[UpdateOne] = []
    for p in profiles:
        doc = dict(p)
        if '_id' in doc:
            doc['_id'] = to_object_id(doc['_id'])
        key = {'candidate_id': doc.get('candidate_id')}
        if not key['candidate_id']:
            # Skip if no stable id
            continue
        prof_ops.append(UpdateOne(key, {'$set': doc}, upsert=True))

    intern_ops: List[UpdateOne] = []
    for it in internships:
        doc = dict(it)
        if '_id' in doc:
            doc['_id'] = to_object_id(doc['_id'])
        key = {'internship_id': doc.get('internship_id')}
        if not key['internship_id']:
            continue
        intern_ops.append(UpdateOne(key, {'$set': doc}, upsert=True))

    user_ops: List[UpdateOne] = []
    for u in login_info:
        doc = dict(u)
        if '_id' in doc:
            doc['_id'] = to_object_id(doc['_id'])
        username = doc.get('username') or doc.get('user')
        if not username:
            continue
        user_ops.append(UpdateOne({'username': username}, {'$set': doc}, upsert=True))

    syn_ops: List[UpdateOne] = []
    # Accept either dict format { key: canonical } or list of {skill, synonyms}
    if isinstance(skills_synonyms, dict):
        # Convert dict into canonical docs
        for alias, canonical in skills_synonyms.items():
            if not isinstance(alias, str) or not isinstance(canonical, str):
                continue
            doc = {
                'alias': alias.strip().lower(),
                'canonical': canonical.strip().lower(),
            }
            syn_ops.append(UpdateOne({'alias': doc['alias']}, {'$set': doc}, upsert=True))
    elif isinstance(skills_synonyms, list):
        # Expect [{"skill":"python", "synonyms":"python, py"}, ...]
        for item in skills_synonyms:
            if not isinstance(item, dict):
                continue
            skill = (item.get('skill') or '').strip().lower()
            syns_raw = item.get('synonyms')
            syn_list = []
            if isinstance(syns_raw, str):
                syn_list = [s.strip().lower() for s in syns_raw.split(',') if s.strip()]
            elif isinstance(syns_raw, list):
                syn_list = [str(s).strip().lower() for s in syns_raw if str(s).strip()]
            # Always include the main skill as its own alias mapping
            if skill:
                syn_list = list(dict.fromkeys([skill] + syn_list))  # unique, keep order
                for alias in syn_list:
                    doc = {'alias': alias, 'canonical': skill}
                    syn_ops.append(UpdateOne({'alias': alias}, {'$set': doc}, upsert=True))

    # Execute in DB
    try:
        if prof_ops:
            db['profiles'].bulk_write(prof_ops, ordered=False)
        if intern_ops:
            db['internships'].bulk_write(intern_ops, ordered=False)
        if user_ops:
            db['login_info'].bulk_write(user_ops, ordered=False)
        if syn_ops:
            db['skills_synonyms'].bulk_write(syn_ops, ordered=False)
    except PyMongoError as e:
        print(f"[fatal] bulk write failed: {e}")
        return 2

    # Create indexes
    try:
        db['profiles'].create_index('candidate_id', unique=True)
        db['profiles'].create_index('name')
        db['internships'].create_index('internship_id', unique=True)
        db['internships'].create_index('skills_required')
        db['login_info'].create_index('username', unique=True)
        db['skills_synonyms'].create_index('alias', unique=True)
        db['skills_synonyms'].create_index('canonical')
    except PyMongoError as e:
        print(f"[warn] index creation issue: {e}")

    # Print summary
    print('--- Migration Summary ---')
    print(f"profiles: {db['profiles'].count_documents({})}")
    print(f"internships: {db['internships'].count_documents({})}")
    print(f"login_info: {db['login_info'].count_documents({})}")
    print(f"skills_synonyms: {db['skills_synonyms'].count_documents({})}")
    print('Done.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
