int leds[4] = {2, 3, 4, 5};
int btns[4] = {A0, A1, A2, A3};

void setup() {
    pinMode(leds[0], OUTPUT);
    pinMode(leds[1], OUTPUT);
    pinMode(leds[2], OUTPUT);
    pinMode(leds[3], OUTPUT);
  // for (int i = 0; i <= 4; i++) {
  //   pinMode(leds[i], OUTPUT);
  //   pinMode(btns[i], INPUT);
  // }
}

void loop() {
    digitalWrite(leds[0], HIGH);
    digitalWrite(leds[1], HIGH);
    digitalWrite(leds[2], HIGH);
    digitalWrite(leds[3], HIGH);
  // for (int i = 0; i <= 4; i++) {
  //   digitalWrite(leds[i], HIGH);
  //   analogRead(btns[i]);
  // }
}
