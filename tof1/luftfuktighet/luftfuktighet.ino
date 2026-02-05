#include <dht.h>
#define dataPin 8

dht DHT; // Creats a DHT object

void setup() {
  Serial.begin(9600);
  Serial.println("Temperature(C);Humidity(%)");
}

void loop() {
  int readData = DHT.read22(dataPin); // DHT22/AM2302

  float t = DHT.temperature;
  float h = DHT.humidity;

  Serial.print(t);
  Serial.print(";");
  Serial.print(h);
  Serial.println("");

  delay(1000);
}
