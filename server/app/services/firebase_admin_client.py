# app/services/firebase_admin_client.py
from __future__ import annotations
import os, firebase_admin
from firebase_admin import credentials, firestore

def get_db():
    if not firebase_admin._apps:
        key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "firebase_key.json")
        try:
            cred = credentials.Certificate(key_path) if os.path.exists(key_path) else credentials.ApplicationDefault()
        except Exception:
            cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)
    return firestore.client()
