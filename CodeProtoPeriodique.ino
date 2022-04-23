/*
  Code du prototype périodique (WEMOS LOLIN32 LITE)
  Par: Biomed3
  Date: XX/XX/2021
  Lien Github: https://github.com/yelmokht/Biomed_3/blob/main/Finale.ino

  Description à mettre

  Connexions à l'ESP32 (WEMOS LOLIN32 LITE):
  -3.3V = 3.3V
  -GND = GND
  -SDA = 33 (ou 21 sur WEMOS LOLIN32)
  -SCL = 32 (ou 22 sur WEMOS LOLIN32)
*/ 

//Import des librairies
#include <Wire.h> //I2C
#include <WiFi.h> //WIFI
#include <WiFiSTA.h> //WIFI
#include <InfluxDb.h> //INFLUXDB
#include "ClosedCube_STS35.h" //Capteur de température (STS35)
#include "MAX30105.h" //Capteur cardiaque (MAX30102)
#include "heartRate.h" //Capteur cardiaque (MAX30102)
#include "time.h" //Timer
#include "driver/adc.h" //ADC
#include <esp_wifi.h> //WiFi

//Définition des constantes
#define INFLUXDB_HOST "influx.biomed.ulb.ovh"
#define INFLUXDB_PORT 80
#define INFLUXDB_DATABASE "biomed3"
#define INFLUXDB_USER "biomed3"
#define INFLUXDB_PASSWORD "Or1nqhDW5ynBvs4a"
#define WIFI_SSID "Sen0uy"
#define WIFI_PASSWORD "31841899098404334204"
#define STS35_I2C_ADDRESS 0x4B
#define DEVICE "WEMOS LOLIN32 Lite"
#define LED_BUILTIN 5

//Initialisation des objets
Influxdb influx(INFLUXDB_HOST, INFLUXDB_PORT); //Connexion à la base InfluxDB
ClosedCube::Sensor::STS35 sts35; //STS35
MAX30105 particleSensor; //MAX30102

//Constantes
const byte RATE_SIZE = 4; //Increase this for more averaging. 4 is good.
const unsigned long interval = 10000; //Intervalle maximale de temps pour se connecter au WiFi ou à la base de données
const float calibration = 5.5; //Valeur ajoutée à la température pour correspondre à celle du corps

//Variables
byte rates[RATE_SIZE]; //Array of heart rates
byte rateSpot = 0;
long lastBeat = 0; //Time at which the last beat occurred
float beatsPerMinute;
int beatAvg;
unsigned long start_time = 0; //Début du timer
unsigned long timer_number; //Temps pour la connexion
bool connected_to_WIFI = false; //Booléen sur la connexion du Wifi
bool acces_to_database = false; //Booléen sur la connexion à la database
int bpm; //Battement cardiaque par minute du patient
float temp; //Température du patient
long rssi; //Puissance du signal WiFi
String local_ip; //Adresse IP Locale  
String mac_adress; //Adresse MAC

//Fonctions

//Timer (OK)
bool IRAM_ATTR timer(unsigned long interval) {
  unsigned long current_time = millis();
  if (start_time==0) {
    start_time = current_time;
  }
  timer_number = (current_time - start_time)/1000;
  Serial.println("Minuteur");
  Serial.println(timer_number);
  return current_time - start_time < interval;
}

//Se connecter au Wifi (OK)
void setupWifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while ((WiFi.status() != WL_CONNECTED) && (timer(interval))) {
    delay(1000);
    }
    rssi = WiFi.RSSI();
    local_ip = WiFi.localIP().toString();
    mac_adress = WiFi.macAddress();
    start_time = 0;
    setConnectedToWifi(WiFi.status());
    timer_number = 0;
}

//T/F (OK)
void setConnectedToWifi(bool x) {
  connected_to_WIFI = x;
  if (timer_number != 10) {
    Serial.println("Connecté au WiFi");
  }
  else {
    Serial.println("Délai de connexion dépassé pour le WiFi");
  }
}

//T/F (OK)
bool getConnectedToWifi() {
  return connected_to_WIFI;
}

//Se connecter à InfluxDB (OK)
void setupInfluxDB(){
  influx.setDbAuth(INFLUXDB_DATABASE, INFLUXDB_USER, INFLUXDB_PASSWORD);
  while (timer(interval) && !influx.validateConnection()) {
    delay(1000);
    }
    start_time = 0;
    setAccessToDatabase(influx.validateConnection());
}

//T/F (OK)
void setAccessToDatabase(bool x) {
   acces_to_database = x;
   if (timer_number != 10) {
    Serial.println("Connecté à InfluxDB");
  }
  else {
    Serial.println("Délai de connexion dépassé pour InfluxDB");
  }
}

//T/F (OK)
bool getAccesToDatabase() {
  return acces_to_database;
}

//Envoyer les mesures à la base de données (OK)
void send_data_database(float t, int b, long r, String l, String m, String d) {
    InfluxData measurement("Experience2");
    Serial.println("Température: ");
    Serial.println(t);
    Serial.println("Battement par minutes: ");
    Serial.println(b);
    Serial.println("RSSI: ");
    Serial.println(r);
    Serial.println("Adresse IP locale: ");
    Serial.println(l);
    Serial.println("Adresse MAC: ");
    Serial.println(m);
    Serial.println("Device: ");
    Serial.println(d);
    measurement.addValue("temp", t);
    measurement.addValue("bpm", b);
    measurement.addValue("rssi", r);
    //measurement.addTag("Adresse IP local", l);
    //measurement.addTag("Adresse MAC", m);
    //measurement.addTag("Appareil", d);
    influx.write(measurement);
}

//Se connecter au STS35 (OK)
void setupSTS35() {
  sts35.address(0x4B);
}

//Prendre la température (OK)
float initializeSTS35() {
  return sts35.readTemperature();
}

//Se connecter au MAX30102 (OK)
void setupMAX30102() {
  byte ledBrightness = 0x7F; //Options: 0=Off to 255=50mA
  byte sampleAverage = 4; //Options: 1, 2, 4, 8, 16, 32
  byte ledMode = 2; //Options: 1 = IR only, 2 = Red + IR on MH-ET LIVE MAX30102 board
  int sampleRate = 200; //Options: 50, 100, 200, 400, 800, 1000, 1600, 3200
  int pulseWidth = 411; //Options: 69, 118, 215, 411
  int adcRange = 16384; //Options: 2048, 4096, 8192, 16384
  Serial.println("Initializing...");
  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)){
    Serial.println("MAX30105 was not found. Please check wiring/power. ");
    while (1);
  }
  Serial.println("Place your index finger on the sensor with steady pressure.");
  particleSensor.setup(ledBrightness, sampleAverage, ledMode, sampleRate, pulseWidth, adcRange); //Configure sensor with these settings
  particleSensor.setPulseAmplitudeRed(0x0A); //Turn Red LED to low to indicate sensor is running
  particleSensor.setPulseAmplitudeGreen(0); //Turn off Green LED
}

//Prendre le bpm (OK)
int initializeMAX30102() {
  while (timer(interval)) {
    long irValue = particleSensor.getIR();

  if (checkForBeat(irValue) == true)
  {
    //We sensed a beat!
    long delta = millis() - lastBeat;
    lastBeat = millis();

    beatsPerMinute = 60 / (delta / 1000.0);

    if (beatsPerMinute < 255 && beatsPerMinute > 20)
    {
      rates[rateSpot++] = (byte)beatsPerMinute; //Store this reading in the array
      rateSpot %= RATE_SIZE; //Wrap variable

      //Take average of readings
      beatAvg = 0;
      for (byte x = 0 ; x < RATE_SIZE ; x++)
        beatAvg += rates[x];
      beatAvg /= RATE_SIZE;
    }
  }

  Serial.print("IR=");
  Serial.print(irValue);
  Serial.print(", BPM=");
  Serial.print(beatsPerMinute);
  Serial.print(", Avg BPM=");
  Serial.print(beatAvg);

  if (irValue < 50000)
    Serial.print(" No finger?");

  Serial.println();
  }
  start_time = 0;
  particleSensor.shutDown();
  return beatAvg;
}


//Lire et stocker les données pour l'envoi des données (OK)
void read_data_from_sensors() {
  bpm = initializeMAX30102();
  temp = initializeSTS35();
  checkTemp(temp);
}

void checkTemp(float t) {
  if (t > 25) {
    temp = t + calibration;
    Serial.println(temp);
  }
}

void lightUpLED() {
  pinMode(LED_BUILTIN, OUTPUT);
  if (temp < 25 || bpm < 30) {
    for (int i = 0; i<4; i++) {
       digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on (HIGH is the voltage level)
       delay(500);                       // wait for a second
       digitalWrite(LED_BUILTIN, LOW);    // turn the LED off by making the voltage LOW
       delay(500);    
    }
  }
}

//Go to deepsleep (OK)
void deep_sleep(int time_in_microseconds) {
  WiFi.disconnect(true); //Eteindre le Wifi pour minimiser la consommation en deep-sleep
  WiFi.mode(WIFI_OFF);//Eteindre le Wifi pour minimiser la consommation en deep-sleep
  adc_power_off(); //Eteindre les ports ADC pour minimiser la consommation en deep-sleep
  esp_wifi_stop(); //Eteindre le Wifi pour minimiser la consommation en deep-sleep
  esp_sleep_enable_timer_wakeup(time_in_microseconds);
  esp_deep_sleep_start();
}

//Setup (OK)
void setup() {
  setCpuFrequencyMhz(80); //Minimisation de la consommation en diminuant la fréquence du CPU
  Serial.begin(115200); //OK
  Wire.begin(33, 32); //OK
  adc_power_on(); //OK
  setupSTS35(); //OK
  setupMAX30102(); //OK
  read_data_from_sensors(); //OK
  //lightUpLED(); //OK
  setupWifi(); //OK
  setupInfluxDB(); //OK
  if (getConnectedToWifi() && getAccesToDatabase()) {
    send_data_database(temp, bpm, rssi, local_ip, mac_adress, DEVICE); //OK
  }
  deep_sleep(270000000); //OK
}

//Loop (OK)
void loop() {
}
