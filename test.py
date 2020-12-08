import firebase_admin
from firebase_admin import credentials, firestore
import statistics
import smtplib
import time
import json
import numpy as np
from sklearn.linear_model import LinearRegression
import datetime
import requests

aTime = []
aTemp = []

nowTS = datetime.datetime.now().timestamp() * 1000
now = datetime.datetime.now()
minsAgoTS = now - datetime.timedelta(minutes=25).timestamp() * 1000
minsAgo = now - datetime.timedelta(minutes=25)

for d in range(5):
    docs = db.collection('usageData').where(
        u'timeTurnedOn', u'>=', minsAgoTS).get()

    usedTime = 0
    for doc in docs:
        # Agrega los segundos que llevan encendidos
        usedTime = usedTime + (now - doc.to_dict()['timeTurnedOn'])/1000
    # Busca dispositvos que se encendieron hace mas de 5 minutos y siguen encendidos
    docs = db.collection('portstates').where(
        u'state', u'==', False).where(u'lastTimeOn', u'<=', nowTS).get()
    for doc in docs:
        usedTime = usedTime + 5  # Suma los 5 minutos que llevan encendidos

    aTime.append(usedTime)

    docs2 = db.collection('sensorReadings').where(
        u'timestamp', u'>=', minsAgo).get()
    aTemp.append(docs2[0].to_dict()['value'])

    minsAgoTS = minsAgo + 300000
    minsAgo = now + datetime.timedelta(minutes=5)

inferency(aTime, aTemp)

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