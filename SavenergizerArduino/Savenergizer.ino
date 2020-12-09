
#if defined(ESP8266)
#include <ESP8266WiFi.h>
#else
#include <WiFi.h>
#endif
#if defined(ESP8266)
#include <ESP8266WebServer.h>
#else
#include <WebServer.h>
#endif
#include <PubSubClient.h>
#include "DHT.h"
#define DHTPIN 35
#define DHTTYPE DHT11

DHT dht(DHTPIN,DHTTYPE);

const char* mqtt_server = "192.168.100.4"; //mqtt server
const char* ssid = "Totalplay-D4A3";
const char* password = "D4A369E35W9Ckc4M";

WiFiClient espClient;
PubSubClient client(espClient); //lib required for mqtthttps://raw.githubusercontent.com/playelek/pinout-doit-32devkitv1/master/pinoutDOIT32devkitv1.png


int LED = 2;
int P1 = 32;
int P2 = 33;
int P3 = 25;
int P4 = 26;
int P5 = 27;
int P6 = 214;
int TEMPIN = 35;

unsigned long ms = 0;
void setup()
{
  Serial.begin(9600);
  Serial.println(F("DHTxx test!"));
  pinMode(LED, OUTPUT);
  pinMode(P1, OUTPUT);
  pinMode(P2, OUTPUT);
  pinMode(P3, OUTPUT);
  pinMode(P4, OUTPUT);
  pinMode(P5, OUTPUT);
  pinMode(P6, OUTPUT);
  //pinMode(TEMPIN, INPUT);
  digitalWrite(LED, HIGH);
  dht.begin();
  WiFi.begin(ssid, password);
  Serial.println("connected");
  client.setServer(mqtt_server, 1883);//connecting to mqtt server
  client.setCallback(callback);
  //delay(5000);
  connectmqtt();
  digitalWrite(LED, LOW);
}

void callback(char* topic, byte* payload, unsigned int length) {   //callback includes topic and payload ( from which (topic) the payload is comming)
  digitalWrite(LED, HIGH);
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  String data = "";
  for (int i = 0; i < length; i++){
    data += (char)payload[i];
  }

  Serial.println(data);
  
  String port = getSplitValue(data, '-', 0);
  String state= getSplitValue(data, '-', 1);

  String portNum = getSplitValue(port, 't', 1);
  
  int p=0;
  switch(portNum.toInt()){
    case 1: p = P1; break;
    case 2: p = P2; break;
    case 3: p = P3; break;
    case 4: p = P4; break;
    case 5: p = P5; break;
    case 6: p = P6; break;
  }
  if (state == "on" || state == "True") //on
  {
    digitalWrite(p, HIGH);
    Serial.println(port + " in pin " + p + " turned on");
  }
  else if (state == "off" || state == "False") //off
  {
    digitalWrite(p, LOW);
    Serial.println(port +  " in pin " + p + " turned off");
  }
  Serial.println();
  digitalWrite(LED, LOW);

}

void reconnect() {
  while (!client.connected()) {
    Serial.println("Attempting MQTT connection...");
    if (client.connect("ESP32")) {
      Serial.println("connected");
      // Once connected, publish an announcement...
      //client.publish("data", "Nodemcu connected to MQTT");
      client.subscribe("states");

    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

void loop()
{
  // put your main code here, to run repeatedly:
  if (!client.connected())
  {
    reconnect();
  }

  // for taking temperature just every 5 minutes
  long currentMs = millis();
  if(ms == 0) {
    ms = currentMs;
  } else if( currentMs - ms >= 300000){
    ms = currentMs;
    
    int temp = random(25,50);
    String sendData = String(temp);
    char copy[3];
    sendData.toCharArray(copy, 3);
    Serial.print("Detected temperature: ");
    Serial.println(temp);
    client.publish("data", copy);
    delay(3000);
  } else {
    Serial.print("Faltan ");
    Serial.print(300-(currentMs - ms)/1000);
    Serial.println(" segundos para la siguiente lectura de temperatura");
  }
 
  client.loop();
}


void connectmqtt()
{
  client.connect("ESP32_clientID");  // ESP will connect to mqtt broker with clientID
  {
    Serial.println("connected to MQTT");
    // Once connected, publish an announcement...

    // ... and resubscribe
    client.subscribe("states"); //topic=Demo
    client.publish("data",  "connected to MQTT");

    if (!client.connected())
    {
      reconnect();
    }
  }
}


String getSplitValue(String data, char separator, int index)
{
    int found = 0;
    int strIndex[] = { 0, -1 };
    int maxIndex = data.length() - 1;

    for (int i = 0; i <= maxIndex && found <= index; i++) {
        if (data.charAt(i) == separator || i == maxIndex) {
            found++;
            strIndex[0] = strIndex[1] + 1;
            strIndex[1] = (i == maxIndex) ? i+1 : i;
        }
    }
    return found > index ? data.substring(strIndex[0], strIndex[1]) : "";
}
