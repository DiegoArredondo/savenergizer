import paho.mqtt.client as mqtt
import firebase_admin
from firebase_admin import credentials, firestore
import statistics
import smtplib
import json
import numpy as np
from sklearn.linear_model import LinearRegression
import datetime
import requests


################################
##### FIREBASE STUFF ###########
################################
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

################################
##### MQTT STUFF ###############
################################
client = mqtt.Client()


################################
##### DB LISTENER ##############
################################
def onPortStateChange(doc_snapshot, changes, read_time):
    for change in changes:
        if change.type.name == 'MODIFIED':
            doc = change.document
            print(u'Received document snapshot: {}'.format(doc.id))
            doc = change.document
            print('CHANGING PORT STATE: {}-{}'.format(doc.id, doc.to_dict()['state']))
            client.publish('states', '{}-{}'.format(doc.id, doc.to_dict()['state']))


################################
##### SENSOR DATA FUNCTIONS ####
################################
def saveData(d):
    if d == "%d":
        return
    data = int(d)
    ts = datetime.datetime.now()
    if dataQuality(data):
        print(u'Received temperature: {} at {}'.format(data, ts))
        doc = db.collection('sensorReadings').document(str(ts).split(".")[0]) .set({
            'value': data,
            'timestamp': ts
        })
        if data > 40:
            print("Sending alert email")
            sendAlert(data, ts)
    else:
        print(u'Received atypical temperature: {} at {}'.format(data, ts))
        doc = db.collection('atypicalData').document(str(ts).split(".")[0]).set({
            'value': data,
            'timestamp': ts
        })

    aTime = []
    aTemp = []

    nowTS = datetime.datetime.now().timestamp() * 1000
    now = datetime.datetime.now()
    minsAgo = now - datetime.timedelta(minutes=25)
    minsAgoTS = minsAgo.timestamp() * 1000

    for d in range(5):
        docs = db.collection('usageData').where(
            u'timeTurnedOn', u'>=', minsAgoTS).get()

        usedTime = 0
        for doc in docs:
            # Agrega los segundos que llevan encendidos
            usedTime = usedTime + (nowTS - doc.to_dict()['timeTurnedOn'])/1000
        # Busca dispositvos que se encendieron hace mas de 5 minutos y siguen encendidos
        docs = db.collection('portstates').where(
            u'state', u'==', False).where(u'lastTimeOn', u'<=', nowTS).get()
        for doc in docs:
            usedTime = usedTime + 5  # Suma los 5 minutos que llevan encendidos

        aTime.append(usedTime)

        docs2 = db.collection('sensorReadings').where(
            u'timestamp', u'<=', minsAgo).get()
        aTemp.append(docs2[0].to_dict()['value'])

        minsAgoTS = minsAgoTS + 300000
        minsAgo = minsAgo + datetime.timedelta(minutes=5)

    inferency(aTime, aTemp)


def dataQuality(data):
    docs = db.collection('sensorReadings').get()
    readings = []
    for r in docs:
        readings.append(r.to_dict()['value'])
    avg = statistics.mean(readings)
    stDev = statistics.stdev(readings)
    print('mean: {}'.format(avg))
    print('stdev: {}'.format(stDev))
    return avg - stDev <= data <= avg + stDev


def sendAlert(data, ts):
    doc = db.collection('alert').document(str(ts).split(".")[0]).set({
        'value': data,
        'timestamp': ts,
        'alertLevel': 'HIGH' if data >= 60 else 'NORMAL'
    })

    gmail_user = 'diego.arredondo.c@gmail.com'
    gmail_password = 'rqbmhjudzzezdehg'

    sent_from = gmail_user
    to = ['diego.arredondo@potros.itson.edu.mx']
    subject = 'Tu Savenergizer se esta sobrecalentando'
    body = 'Hola!\n Tu Savenergizar se esta sobrecalentando y se ha detectado que la temperatura subio hasta {}C hace unos segundos. Por favor revisa tu dispositivo y si el calentamiento continua, desconectalo por unos minutos o hasta que su temperatura disminuya\n\n - El equipo de Savenergizer'.format(data)

    email_text = """\
    From: %s
    To: %s
    Subject: %s

    %s
    """ % (sent_from, ", ".join(to), subject, body)

    serverToken = 'AAAAV8NxifI:APA91bGTGjeJSTDyRZS8W5ZdMCr15gWYEE1LHCUaggtJ31uPGGpt2YSe7N32TgSVlBRqwZ70srvFAbqdqvJpPkiQ0Z9yNtmBqV3YxVErASjuUbmM-oUSI55H8wFNYnNM2NqbKu_JF6gt'
    deviceToken = '5QiZ5z_SByv-gJ6BlzxBA:APA91bElDEStTDo6LAh9d_Ubmi1s0LSbHD7Juu9b_eq1tJ3DBfGaS3yiqqkUsi3kHASkvA6VJf25MaLh3HDIDsWL0hTZMKkfEmOxdoUSMMfDgOaBPOX6fWwMU-7XvUSGfrU4S_o8ZAcw'

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'key=' + serverToken,
      }

    body = {
          'notification': {'title': 'Tu Savenergizer se esta sobrecalentando',
                            'body': 'Hola!\n Tu Savenergizar se esta sobrecalentando y se ha detectado que la temperatura subio hasta {}C hace unos segundos. Por favor revisa tu dispositivo y si el calentamiento continua, desconectalo por unos minutos o hasta que su temperatura disminuya\n\n - El equipo de Savenergizer'.format(data)
                            },
          'to':
              deviceToken,
          'priority': 'high',
        #   'data': dataPayLoad,
        }
    response = requests.post("https://fcm.googleapis.com/fcm/send",headers = headers, data=json.dumps(body))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(sent_from, to, email_text)
        server.close()

        print('Email sent!')
    except Exception as e:
        print('Ocurrió el siguiente error: {}'.format(e))

#Inferencia - temperatura según el tiempo activo
def inferency(aTime, aTemp):

    x = np.array(aTime).reshape((-1, 1))
    y = np.array(aTemp)

    model = LinearRegression().fit(x, y)

    r_sq = model.score(x, y)

    longitudArregloTiempo = len(aTime)
    horaSiguiente = aTime[longitudArregloTiempo-1]
    xN = []

    for d in range (5):
        horaSiguiente = horaSiguiente + 1
        xN.append(horaSiguiente)

        xNuevas = np.array(xN).reshape((-1, 1))
        yNuevas = model.predict(xNuevas)

    for x in range(len(xNuevas)):
        print('Hora: {} predicción de temperatura: {temperatura:.1f}°'.format(xNuevas[x], temperatura = yNuevas[x]))

    client.publish("inferences", "{temperatura:.1f}".format(temperatura = yNuevas[0]))


################################
##### MQTT FUNCTIONS ###########
################################
def on_connect(client, userdata, flags, rc):
    print("Connecting to server - "+str(rc))
    client.subscribe("data")

def on_message(client, userdata, msg):
    print(f"Received data: {msg.topic} - {str(msg.payload)}")
    saveData(str(msg.payload).split("'")[1])

def on_publish(client, obj, mid):
    print("Sent data: " + str(mid))

def on_subscribe(client, obj, mid, granted_qos):
    print("Subscribed: " + str(client))


db.collection(u'portStates').on_snapshot(onPortStateChange)
client.on_connect = on_connect
client.on_message = on_message
client.on_subscribe = on_subscribe
client.on_publish = on_publish
client.connect("localhost", 1883, 60)
client.loop_forever()


