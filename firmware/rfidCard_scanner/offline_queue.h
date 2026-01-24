#ifndef OFFLINE_QUEUE_H
#define OFFLINE_QUEUE_H

#include "FS.h"
#include "SPIFFS.h"
#include <ArduinoJson.h>
#include "network_manager.h"

#define QUEUE_FILE "/queue.txt"

void setupQueue() {
  if (!SPIFFS.begin(true)) {
    Serial.println("An Error has occurred while mounting SPIFFS");
    return;
  }
}

void saveToQueue(String uid, bool accessGranted, String timestamp) {
  File file = SPIFFS.open(QUEUE_FILE, FILE_APPEND);
  if (!file) {
    Serial.println("Failed to open file for appending");
    return;
  }

  // Create simple JSON line
  StaticJsonDocument<256> doc;
  doc["card_uid"] = uid;
  doc["status"] = accessGranted;
  if(timestamp.length() > 0) {
    // We store as created_at generically, logic in network_manager will handle mapping
    // But to be safe and consistent with previous queue logic:
    doc["created_at"] = timestamp; 
  }

  if (serializeJson(doc, file) == 0) {
    Serial.println("Failed to write to file");
  }
  file.println(); // Newline separator
  file.close();
  Serial.println("Saved to offline queue");
}

void processQueue() {
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }

  if (!SPIFFS.exists(QUEUE_FILE)) {
    return;
  }

  File file = SPIFFS.open(QUEUE_FILE, FILE_READ);
  if (!file) {
    return;
  }

  // We need to read all lines, try to sync them, and keep those that fail.
  // Since we can't easily modify a file in place, we write to a temp file.
  
  String tempContent = "";
  bool failureOccurred = false;
  int count = 0;

  while (file.available()) {
    String line = file.readStringUntil('\n');
    line.trim();
    if (line.length() == 0) continue;

    StaticJsonDocument<256> doc;
    DeserializationError error = deserializeJson(doc, line);

    if (!error) {
      String uid = doc["card_uid"];
      bool status = doc["status"];
      String timestamp = "";
      if (doc.containsKey("created_at")) {
        const char* t = doc["created_at"];
        if (t) timestamp = String(t);
      }
      
      // Pass the stored timestamp and status
      if (sendLogToSupabase(uid, status, timestamp)) {
        Serial.println("Synced offline log for " + uid);
        count++;
      } else {
        // Keep line
        tempContent += line + "\n";
        failureOccurred = true;
      }
    }
  }
  file.close();

  if (count > 0) {
    if (!failureOccurred && tempContent.length() == 0) {
      // All synced, delete file
      SPIFFS.remove(QUEUE_FILE);
    } else {
      // Rewrite remaining
      File fileWrite = SPIFFS.open(QUEUE_FILE, FILE_WRITE);
      if (fileWrite) {
        fileWrite.print(tempContent);
        fileWrite.close();
      }
    }
    Serial.print("Processed ");
    Serial.print(count);
    Serial.println(" offline logs.");
  }
}

#endif
