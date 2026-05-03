#include <SPI.h>
#include <MFRC522.h>
#include "esp_log.h"
#include "secrets.h"
#include "debug.h"
#include "access_control.h"
#include "network_manager.h"
#include "offline_queue.h"
#include "card_manager.h"

static int _null_log(const char*, va_list) { return 0; }

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
  esp_log_set_vprintf(_null_log);      // Null the esp_log vprintf handler before anything else
  Serial.setDebugOutput(false);

  // Init Hardware
  SPI.begin();
  rfid.PCD_Init();
  setupAccessControl();
  setupQueue(); // Initializes SPIFFS which card_manager also uses
  SPIFFS.remove(QUEUE_FILE); // Clear any stale queue accumulated before direct-send was enabled

  Serial.println("\n--- School Access System v2.1 (Dynamic Sync) ---");
  
  // Load cached cards first
  loadCardsFromFile();

  // Connect WiFi
  setupWiFi();
  esp_log_set_vprintf(_null_log);      // Re-apply: WiFi.begin() may re-enable esp_log output

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
  unsigned long now = millis();

  // 1. NFC Check — always runs first so background tasks never gate card scanning
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
    // Background Tasks (only while idle)
    if (now - lastSyncTime > SYNC_INTERVAL) {
      syncCards();
    }
    if (now - lastQueueProcessTime > QUEUE_INTERVAL) {
      lastQueueProcessTime = now;
      if (WiFi.status() == WL_CONNECTED) {
        processQueue();
      }
    }
    delay(50);
    return;
  }

  // 2. Read UID
  String uidStr = "0x";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) uidStr += "0";
    uidStr += String(rfid.uid.uidByte[i], HEX);
  }
  DBG_VAL("Scanned UID: ", uidStr);

  // 3. Check authorization
  bool access = isCardAuthorized(uidStr);
  String timestamp = getISOTime();

  if (!access) {
    // Unauthorized — red briefly, queue the log, no live sync
    denyAccess();
    saveToQueue(uidStr, false, timestamp);
  } else {
    // Authorized — green on immediately, stays on while sync runs
    indicateAccessGranted();

    int code = -1;
    if (WiFi.status() == WL_CONNECTED) {
      code = sendLogToSupabase(uidStr, true, timestamp);
    }

    if (code >= 200 && code < 300) {
      indicateSyncSuccess();
    } else {
      indicateSyncFailure();
      // Queue for retry on transient failures; permanent 4xx rejections are discarded
      if (!(code >= 400 && code < 500)) {
        saveToQueue(uidStr, true, timestamp);
      }
    }
  }

  // 7. Reset Reader
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
  delay(1000);
  rfid.PCD_Init();
}