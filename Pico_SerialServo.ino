#include <Arduino.h>
#include <Servo.h>

//////////////////// USER SETTINGS ////////////////////
const int   SERVO_PIN      = 15;     // GP15 (change if needed)
const int   OPEN_US        = 1500;   // tune to your "open" position
const int   CLOSE_US       = 780;    // tune to your "close" position
const unsigned long AUTO_CLOSE_MS = 3000; // 3s auto-close; 0 = disabled
const unsigned long BAUDRATE = 115200;
///////////////////////////////////////////////////////

Servo gate;
String lineBuf;
unsigned long lastOpenMillis = 0;
bool isOpen = false;

void moveUS(int us) {
  // Standard hobby servo expects ~500–2500 µs at 50 Hz
  gate.writeMicroseconds(us);
}

void doOpen() {
  moveUS(OPEN_US);
  isOpen = true;
  if (AUTO_CLOSE_MS > 0) lastOpenMillis = millis();
  Serial.println(F("OK OPEN"));
}

void doClose() {
  moveUS(CLOSE_US);
  isOpen = false;
  lastOpenMillis = 0;
  Serial.println(F("OK CLOSE"));
}

void handleCommand(const String& raw) {
  String cmd = raw;
  cmd.trim();                  // remove CR/LF + spaces
  cmd.toUpperCase();

  if (cmd == "OPEN") {
    doOpen();
  } else if (cmd == "CLOSE") {
    doClose();
  } else if (cmd.startsWith("SET ")) {
    // SET <us>
    long us = cmd.substring(4).toInt();
    if (us >= 400 && us <= 2600) {
      moveUS((int)us);
      Serial.print(F("OK SET "));
      Serial.println(us);
    } else {
      Serial.println(F("ERR SET range 400..2600"));
    }
  } else if (cmd == "PING") {
    Serial.println(F("PONG"));
  } else if (cmd.length() > 0) {
    Serial.print(F("ERR Unknown: "));
    Serial.println(cmd);
  }
}

void setup() {
  Serial.begin(BAUDRATE);
  // wait for USB serial (optional small delay; don’t block forever)
  delay(500);

  gate.attach(SERVO_PIN);   // default 50 Hz
  doClose();

  Serial.println(F("Pico Serial Servo ready. Commands: OPEN, CLOSE, SET <us>, PING"));
}

void loop() {
  // ---- Non-blocking line reader ----
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\r') continue;         // ignore CR
    if (c == '\n') {
      handleCommand(lineBuf);
      lineBuf = "";
    } else {
      if (lineBuf.length() < 100) lineBuf += c;
    }
  }

  // ---- Auto-close timer ----
  if (AUTO_CLOSE_MS > 0 && isOpen) {
    unsigned long now = millis();
    if (now - lastOpenMillis >= AUTO_CLOSE_MS) {
      doClose();
    }
  }
}
