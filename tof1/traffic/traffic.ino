int red = 13;
int yellow = 11;
int green = 9;

void setup() {
  pinMode(red, OUTPUT);
  pinMode(yellow, OUTPUT);
  pinMode(green, OUTPUT);
}

void loop() {
  int d = 1000;
  digitalWrite(green, HIGH);
  delay(d);
  digitalWrite(green, LOW);
  digitalWrite(yellow, HIGH);
  delay(d);
  digitalWrite(yellow, LOW);
  digitalWrite(red, HIGH);
  delay(d);
  digitalWrite(yellow, HIGH);
  delay(d);
  digitalWrite(yellow, LOW);
  digitalWrite(red, LOW);

  // digitalWrite(yellow, LOW);
  // digitalWrite(red, HIGH);
  // delay(d);
  // digitalWrite(red, LOW);
  // digitalWrite(yellow, HIGH);
  // delay(d);
  // digitalWrite(yellow, LOW);
  // digitalWrite(green, HIGH);
  // delay(d);
  // digitalWrite(yellow, HIGH);
  // digitalWrite(green, LOW);
  // delay(d);
}
