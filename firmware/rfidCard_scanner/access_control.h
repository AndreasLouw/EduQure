#ifndef ACCESS_CONTROL_H
#define ACCESS_CONTROL_H

#include <Arduino.h>

// #define RELAY_PIN 26
// #define BUZZER_PIN 25
#define red_led 25
#define green_led 26

void setupAccessControl() {
  // pinMode(RELAY_PIN, OUTPUT);
  // digitalWrite(RELAY_PIN, HIGH); // Active LOW -> HIGH = OFF
  // pinMode(BUZZER_PIN, OUTPUT);
  pinMode(red_led, OUTPUT);
  digitalWrite(red_led, LOW); // Ensure Red LED starts OFF
  pinMode(green_led, OUTPUT);
  digitalWrite(green_led, LOW); // Ensure Green LED starts OFF
}

void grantAccess() {
  Serial.println("ACCESS GRANTED");
  
  // "Happy" Tune
  // tone(BUZZER_PIN, 2000, 100); 
  // delay(150);
  // tone(BUZZER_PIN, 2500, 150);
  digitalWrite(green_led, HIGH);
  delay(1000);
  digitalWrite(green_led, LOW);

  // Unlock
  // digitalWrite(RELAY_PIN, LOW);   // Relay ON
  // delay(3000);                    // ON for 3 sec (original was 5 in Python, 3 in CPP)
  // digitalWrite(RELAY_PIN, HIGH);  // Relay OFF
}

void denyAccess() {
  Serial.println("ACCESS DENIED");
  
  // "Denied" Tune
  // tone(BUZZER_PIN, 150, 500);
  digitalWrite(red_led, HIGH);
  delay(1000); 
  digitalWrite(red_led, LOW);
}

#endif
