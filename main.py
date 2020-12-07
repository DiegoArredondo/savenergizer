import paho.mqtt.client as mqtt
import firebase_admin
from firebase_admin import credentials, firestore
import statistics
import smtplib
import time
import json


################################
##### FIREBASE STUFF ###########
################################
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

gotData = False
P1 = False
P2 = False
P3 = False
P4 = False
P5 = False
P6 = False

################################
##### MQTT STUFF ###############
################################
client = mqtt.Client()


################################
##### DB LISTENER ##############
################################
def onPortStateChange(doc_snapshot, changes, read_time):
    for doc in doc_snapshot:
        print(u'Received document snapshot: {}'.format(doc.id))
        for change in changes:
            if change.type.name == 'MODIFIED':
                if not gotData:
                    if(doc.id == "port1"):
                        P1 = doc.to_dict()['state']
                        break
                    elif(doc.id == "port2"):
                        P2 = doc.to_dict()['state']
                        break
                    elif(doc.id == "port3"):
                        P3 = doc.to_dict()['state']
                        break
                    elif(doc.id == "port4"):
                        P4 = doc.to_dict()['state']
                        break
                    elif(doc.id == "port5"):
                        P5 = doc.to_dict()['state']
                        break
                    elif(doc.id == "port6"):
                        P6 = doc.to_dict()['state']
                        gotData = True
                        break

                updated = False
                porToUpdate = "none"
                doc = change.document
                print('{}-{}'.format(doc.id, doc.to_dict()['state']))
                if not gotData:
                    if (doc.id == "port1"):
                        if doc.to_dict()['state'] != P1:
                            P1 = doc.to_dict()['state']
                            different = True
                        break
                    elif (doc.id == "port2"):
                        if doc.to_dict()['state'] != P2:
                            P2 = doc.to_dict()['state']
                            different = True
                        break
                    elif (doc.id == "port3"):
                        if doc.to_dict()['state'] != P3:
                            P3 = doc.to_dict()['state']
                            different = True
                        break
                    elif (doc.id == "port4"):
                        if doc.to_dict()['state'] != P4:
                            P4 = doc.to_dict()['state']
                            different = True
                        break
                    elif (doc.id == "port5"):
                        if doc.to_dict()['state'] != P5:
                            P5 = doc.to_dict()['state']
                            different = True
                        break
                    elif (doc.id == "port6"):
                        if doc.to_dict()['state'] != P6:
                            P6 = doc.to_dict()['state']
                            different = True
                        gotData = True
                        break
                if different:
                    client.publish('states', '{}-{}'.format(doc.id, doc.to_dict()['state']))


################################
##### SENSOR DATA FUNCTIONS ####
################################
def saveData(d):
    if d == "%d":
        return
    data = int(d)
    ts = time.time()
    if dataQuality(data):
        print(u'Received temperature: {} at {}'.format(data, ts))
        doc = db.collection('sensorReadings').document(str(ts).split(".")[0]) .set({
            'value': data,
            'timestamp': ts
        })
        if data > 50:
            print("Sending alert email")
            sendAlert(data, ts)
    else:
        print(u'Received atypical temperature: {} at {}'.format(data, ts))
        doc = db.collection('atypicalData').document(str(ts).split(".")[0]).set({
            'value': data,
            'timestamp': ts
        })


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

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(sent_from, to, email_text)
        server.close()

        print('Email sent!')
    except Exception as e:
        print('Ocurrió el siguiente error: {}'.format(e))


################################
##### MQTT FUNCTIONS ###########
################################
def on_connect(client, userdata, flags, rc):
    print("Connecting to server - "+str(rc))
    client.subscribe("data")

def on_message(client, userdata, msg):
    print(f"Received data: {msg.topic} - {str(msg.payload)}")
    #saveData(str(msg.payload).split("'")[1])

def on_publish(client, obj, mid):
    print("Sent data: " + str(mid))

def on_subscribe(client, obj, mid, granted_qos):
    print("Subscribed: " + str(client))


#db.collection(u'portStates').on_snapshot(onPortStateChange)
client.on_connect = on_connect
client.on_message = on_message
client.on_subscribe = on_subscribe
client.on_publish = on_publish
client.connect("localhost", 1883, 60)
client.publish("states", "port1-off")
client.publish("states", "port2-off")
client.publish("states", "port3-off")
client.publish("states", "port4-off")
client.publish("states", "port5-off")
client.publish("states", "port6-off")
client.loop_forever()


