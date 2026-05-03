#ifndef OFFLINE_QUEUE_H
#define OFFLINE_QUEUE_H

#include "FS.h"
#include "SPIFFS.h"
#include <ArduinoJson.h>
#include "network_manager.h"
#include "debug.h"

#define QUEUE_FILE "/queue.txt"

void setupQueue() {
  if (!SPIFFS.begin(true)) {
    Serial.println("ERROR: Failed to mount SPIFFS");
    return;
  }
}

void saveToQueue(String uid, bool accessGranted, String timestamp) {
  File file = SPIFFS.open(QUEUE_FILE, FILE_APPEND);
  if (!file) {
    Serial.println("ERROR: Failed to open queue file");
    return;
  }

  StaticJsonDocument<256> doc;
  doc["card_uid"] = uid;
  doc["status"] = accessGranted;
  if (timestamp.length() > 0) doc["created_at"] = timestamp;

  if (serializeJson(doc, file) == 0) {
    Serial.println("ERROR: Failed to write queue entry");
  } else {
    DBG("Queued log for " + uid);
  }
  file.println();
  file.close();
}

void processQueue() {
  if (WiFi.status() != WL_CONNECTED) return;
  if (!SPIFFS.exists(QUEUE_FILE)) return;

  File file = SPIFFS.open(QUEUE_FILE, FILE_READ);
  if (!file) return;

  // Process up to MAX_BATCH entries per cycle to keep the main loop responsive.
  // Stop on first transient failure — server is likely down.
  const int MAX_BATCH = 2;
  String tempContent = "";
  bool failureOccurred = false;
  int synced = 0;
  int discarded = 0;

  while (file.available()) {
    String line = file.readStringUntil('\n');
    line.trim();
    if (line.length() == 0) continue;

    if (failureOccurred || (synced + discarded) >= MAX_BATCH) {
      tempContent += line + "\n";
      continue;
    }

    StaticJsonDocument<256> doc;
    DeserializationError err = deserializeJson(doc, line);
    if (err) {
      DBG_VAL("Skipping malformed queue entry: ", err.c_str());
      discarded++;
      continue;
    }

    String uid = doc["card_uid"];
    bool status = doc["status"];
    String timestamp = "";
    if (doc.containsKey("created_at")) {
      const char* t = doc["created_at"];
      if (t) timestamp = String(t);
    }

    int code = sendLogToSupabase(uid, status, timestamp);
    if (code >= 200 && code < 300) {
      DBG("Synced queued log for " + uid);
      synced++;
    } else if (code >= 400 && code < 500) {
      // Permanent rejection — retrying won't help, discard.
      Serial.println("Discarding log for " + uid + " (HTTP " + String(code) + ")");
      discarded++;
    } else {
      // Transient failure — stop this cycle, retry next time.
      DBG_VAL("Queue flush paused, will retry. Code: ", code);
      tempContent += line + "\n";
      failureOccurred = true;
    }
  }
  file.close();

  int processed = synced + discarded;
  if (processed > 0) {
    if (!failureOccurred && tempContent.length() == 0) {
      SPIFFS.remove(QUEUE_FILE);
    } else {
      File fw = SPIFFS.open(QUEUE_FILE, FILE_WRITE);
      if (fw) { fw.print(tempContent); fw.close(); }
    }
    DBG_VAL("Queue: synced=", synced);
    DBG_VAL("Queue: discarded=", discarded);
  }
}

#endif
