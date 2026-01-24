#ifndef CARD_MANAGER_H
#define CARD_MANAGER_H

#include "FS.h"
#include "SPIFFS.h"
#include <ArduinoJson.h>
#include <vector>

#define CARDS_FILE "/cards.json"

// Global list of authorized cards
std::vector<String> authorizedCards;

void saveCardsToFile() {
  File file = SPIFFS.open(CARDS_FILE, FILE_WRITE);
  if (!file) {
    Serial.println("Failed to open cards file for writing");
    return;
  }

  // Calculate capacity roughly: 2048 bytes should hold plenty of UIDs
  DynamicJsonDocument doc(2048);
  JsonArray array = doc.to<JsonArray>();

  for (const String& uid : authorizedCards) {
    array.add(uid);
  }

  if (serializeJson(doc, file) == 0) {
    Serial.println("Failed to write cards to file");
  } else {
    Serial.println("Cards saved to local storage.");
  }
  file.close();
}

void loadCardsFromFile() {
  if (!SPIFFS.exists(CARDS_FILE)) {
    Serial.println("No local cards file found.");
    return;
  }

  File file = SPIFFS.open(CARDS_FILE, FILE_READ);
  if (!file) {
    Serial.println("Failed to open cards file for reading");
    return;
  }

  DynamicJsonDocument doc(4096); // Allow a bit more for reading
  DeserializationError error = deserializeJson(doc, file);

  if (error) {
    Serial.print("Failed to parse cards file: ");
    Serial.println(error.c_str());
    file.close();
    return;
  }

  JsonArray array = doc.as<JsonArray>();
  authorizedCards.clear();
  for (JsonVariant v : array) {
    authorizedCards.push_back(v.as<String>());
  }
  
  Serial.print("Loaded ");
  Serial.print(authorizedCards.size());
  Serial.println(" cards from local storage.");
  
  file.close();
}

bool isCardAuthorized(String uid) {
  for (const String& authorizedUid : authorizedCards) {
    if (uid.equalsIgnoreCase(authorizedUid)) {
      return true;
    }
  }
  return false;
}

void refreshCards(String jsonPayload) {
  if (jsonPayload.length() == 0) return;

  DynamicJsonDocument doc(8192);
  DeserializationError error = deserializeJson(doc, jsonPayload);

  if (error) {
    Serial.print("Failed to parse card JSON: ");
    Serial.println(error.c_str());
    return;
  }

  JsonArray array = doc.as<JsonArray>();
  std::vector<String> newCards;
  
  for (JsonVariant v : array) {
    // Supabase returns object like {"card_uid": "..."}
    if (v.containsKey("card_uid")) {
        newCards.push_back(v["card_uid"].as<String>());
    }
  }

  if (newCards.size() > 0) {
    authorizedCards = newCards;
    Serial.print("Updated authorized cards list. Count: ");
    Serial.println(authorizedCards.size());
    saveCardsToFile();
  } else {
    Serial.println("Warning: Fetched list was empty or invalid format.");
  }
}

#endif
