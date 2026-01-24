#include <SPI.h>
#include <MFRC522.h>
#include "secrets.h"
#include "access_control.h"
#include "network_manager.h"
#include "offline_queue.h"
#include "card_manager.h"

#define SS_PIN 5
#define RST_PIN 22

MFRC522 rfid(SS_PIN, RST_PIN);

unsigned long lastQueueProcessTime = 0;
const unsigned long QUEUE_INTERVAL = 60000; // Check every 60s

unsigned long lastSyncTime = 0;
const unsigned long SYNC_INTERVAL = 3600000; // Check every 1 hour (3600 * 1000)

void syncCards() {
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("Syncing cards from DB...");
    String json = fetchCardsJSON();
    refreshCards(json);
    lastSyncTime = millis();
  }
}

void setup() {
  Serial.begin(115200);
  
  // Init Hardware
  SPI.begin();
  rfid.PCD_Init();
  setupAccessControl();
  setupQueue(); // Initializes SPIFFS which card_manager also uses

  Serial.println("\n--- School Access System v2.1 (Dynamic Sync) ---");
  
  // Load cached cards first
  loadCardsFromFile();

  // Connect WiFi
  setupWiFi(); 
  
  // Initial Sync
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("System Online");
    syncCards();
  } else {
    Serial.println("System Offline - Using cached cards");
  }
  
  rfid.PCD_DumpVersionToSerial();
  Serial.println("Scan your RFID card...");
  grantAccess();
}

void loop() {
  // 1. Background Tasks
  unsigned long now = millis();
  
  // Queue Processing
  if (now - lastQueueProcessTime > QUEUE_INTERVAL) {
    lastQueueProcessTime = now;
    if (WiFi.status() == WL_CONNECTED) {
      processQueue();
    }
  }

  // Card Sync
  if (now - lastSyncTime > SYNC_INTERVAL) {
    syncCards();
  }

  // 2. NFC Check
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
    delay(50); 
    return;
  }

  // 3. Read UID
  String uidStr = "0x";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) uidStr += "0";
    uidStr += String(rfid.uid.uidByte[i], HEX);
  }
  Serial.print("scanned UID: ");
  Serial.println(uidStr);

  // 4. Validate
  bool access = isCardAuthorized(uidStr);

  // 5. Act
  if (access) {
    grantAccess();
  } else {
    denyAccess();
  }

  // 6. Log (Sync or Queue)
  String timestamp = getISOTime(); 
  
  if (!sendLogToSupabase(uidStr, access, timestamp)) {
    saveToQueue(uidStr, access, timestamp);
  }

  // 7. Reset Reader
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
  delay(1000);
  rfid.PCD_Init();
}