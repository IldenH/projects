int red = 5;
int green = 6;
int button = 2;

void setup() {
  pinMode(red, OUTPUT);
  pinMode(green, OUTPUT);
  pinMode(button, INPUT);
}

void loop() {
  handleButton();
  handleLeds();
}

int buttonState = 0;
int lastButtonState = 0;
bool redState = false;

void handleButton() {
  buttonState = digitalRead(button);
  if (buttonState == HIGH && lastButtonState == LOW) {
    redState = !redState;
    delay(50);
  }
  lastButtonState = buttonState;
}


int brightness = 0;
int fadeAmount = 1;
unsigned long lastUpdate = 0;
const int fadeDelay = 5;

void handleLeds() {
  unsigned long now = millis();
  if (now - lastUpdate >= fadeDelay) {
    lastUpdate = now;

    brightness += fadeAmount;

    if (brightness <= 0 || brightness >= 255) {
      fadeAmount = -fadeAmount;
    }

    if (redState) {
      analogWrite(red, brightness);
      digitalWrite(green, 1);
    } else {
      analogWrite(green, brightness);
      digitalWrite(red, 1);
    }
  }
}
