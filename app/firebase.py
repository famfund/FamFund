import os
import firebase_admin
from firebase_admin import credentials, firestore

# Global variable to hold Firestore client
db = None

def initialize_firebase():
    global db
    if not firebase_admin._apps:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        FIREBASE_CREDENTIALS = os.path.join(BASE_DIR, "firebase_config.json")
        cred = credentials.Certificate(FIREBASE_CREDENTIALS)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
