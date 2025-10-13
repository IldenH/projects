int leds[4] = {2, 3, 4, 5};
int btns[4] = {12, 11, 10, 9};

const int patternLength = 4;
int pattern[patternLength] = {0,1,3,2};

void setup() {
  for (int i = 0; i < 4; i++) {
    pinMode(leds[i], OUTPUT);
    pinMode(btns[i], INPUT_PULLUP);
  }
}

void blink(int led) {
  digitalWrite(led, HIGH);
  delay(500);
  digitalWrite(led, LOW);
}

void allLeds(int state) {
  for (int i = 0; i < 4; i++) {
    digitalWrite(leds[i], state);
  }
  delay(1000);
}

int waitForButton() {
  while (true) {
    for (int i = 0; i < 4; i++) {
      if (digitalRead(btns[i]) == LOW) {
        blink(leds[i]);
        while (digitalRead(btns[i]) == LOW);
        return i;
      }
    }
  }
}

void loop() {
  for (int i = 0; i < patternLength; i++) {
    blink(leds[pattern[i]]);
  }
  for (int i = 0; i < patternLength; i++) {
    int guess = waitForButton();
    if (guess != pattern[i]) {
      allLeds(LOW);
      return;
    }
  }
  allLeds(HIGH);
  allLeds(LOW);
}
