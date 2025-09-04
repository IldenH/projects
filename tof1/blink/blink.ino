void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(7, OUTPUT);
  pinMode(6, OUTPUT);
}

void loop() {
  int d = 300;
  digitalWrite(7, HIGH);
  digitalWrite(6, LOW);
  delay(d);
  digitalWrite(7, LOW);
  digitalWrite(6, HIGH);
  delay(d);
}
