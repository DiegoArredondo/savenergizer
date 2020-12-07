import time
import firebase_admin
from firebase_admin import credentials, firestore, auth

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

ts = time.time()
db.collection(u'sensorReadings').document(str(ts).split(".")[0]).set({
    u'timestamp': ts,
    u'value': 27.3,
})

# Create a callback on_snapshot function to capture changes
def on_snapshot(doc_snapshot, changes, read_time):
    for doc in doc_snapshot:
        print(u'Received document snapshot: {}'.format(doc.id))

db.collection(u'sensorReadings').document(u'1603826384').on_snapshot(on_snapshot)
