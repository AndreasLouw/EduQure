#ifndef NETWORK_MANAGER_H
#define NETWORK_MANAGER_H

#include <WiFi.h>
#include <HTTPClient.h>
#include "secrets.h"
#include "time.h"

// Time settings for South Africa (UTC+2)
const char* ntpServer = "pool.ntp.org";
const long  gmtOffset_sec = 7200;
const int   daylightOffset_sec = 0;

void setupWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  // Non-blocking wait (sort of, we do want to wait initially)
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 15000) {
    delay(500);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi Connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    
    // Init Time
    configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
    Serial.println("Waiting for time sync...");
    // Give it a moment to sync
    start = millis();
    struct tm timeinfo;
    // Try for 5 seconds to sync time
    while (!getLocalTime(&timeinfo) && millis() - start < 5000) {
        Serial.print(".");
        delay(100);
    }
    Serial.println("\nTime synced.");
    
  } else {
    Serial.println("\nWiFi Connection Failed (Continuing in Offline Mode)");
  }
}

String getISOTime() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    Serial.println("Failed to obtain time");
    return ""; // Return empty if invalid
  }
  
  char timeStringBuff[30]; 
  // Format: 2026-01-17T15:09:58
  strftime(timeStringBuff, sizeof(timeStringBuff), "%Y-%m-%dT%H:%M:%S", &timeinfo);
  
  // Append Timezone manually since specifier %z might vary in format
  // For SAST (UTC+2), we can append "+02:00"
  String timeStr = String(timeStringBuff) + "+02:00";
  return timeStr;
}

bool sendLogToSupabase(String uid, bool accessGranted, String timestamp) {
  if (WiFi.status() != WL_CONNECTED) {
    return false;
  }

  HTTPClient http;
  
  // Construct URL with robust slash handling
  String baseUrl = String(SUPABASE_URL);
  if (baseUrl.endsWith("/")) {
    baseUrl.remove(baseUrl.length() - 1);
  }
  
  String url;
  String payload;
  
  if (accessGranted) {
     // Successful access -> access_logs
     url = baseUrl + "/rest/v1/access_logs";
     
     // Payload: card_uid, lock, status, created_at
     // Note: status is always true here
     payload = "{\"card_uid\":\"" + uid + "\", \"lock\":\"" + String(LOCK_ID) + "\", \"status\":true";
     
     if (timestamp.length() > 0) {
       payload += ", \"created_at\":\"" + timestamp + "\"";
     }
     payload += "}";
     
  } else {
     // Denied access -> unidentified_cards
     url = baseUrl + "/rest/v1/unidentified_cards";
     
     // Payload: card_uid, lock, created_at
     payload = "{\"card_uid\":\"" + uid + "\", \"lock\":\"" + String(LOCK_ID) + "\"";
     
     if (timestamp.length() > 0) {
       payload += ", \"created_at\":\"" + timestamp + "\"";
     }
     payload += "}";
  }
  
  http.begin(url);
  http.addHeader("apikey", SUPABASE_KEY);
  http.addHeader("Authorization", "Bearer " + String(SUPABASE_KEY));
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Prefer", "return=minimal");

  int httpResponseCode = http.POST(payload);
  
  bool success = false;
  if (httpResponseCode >= 200 && httpResponseCode < 300) {
    Serial.println("Supabase Sync Success: " + String(httpResponseCode));
    success = true;
  } else {
    Serial.print("Supabase Sync Error: ");
    Serial.println(httpResponseCode);
    Serial.println("Payload: " + payload);
    String response = http.getString();
    Serial.println("Response: " + response);
  }

  http.end();
  return success;
}



String fetchCardsJSON() {
  if (WiFi.status() != WL_CONNECTED) return "";
  
  HTTPClient http;
  String baseUrl = String(SUPABASE_URL);
  if (baseUrl.endsWith("/")) baseUrl.remove(baseUrl.length() - 1);
  
  String url = baseUrl + "/rest/v1/persons?select=card_uid";
  
  http.begin(url);
  http.addHeader("apikey", SUPABASE_KEY);
  http.addHeader("Authorization", "Bearer " + String(SUPABASE_KEY));
  
  int code = http.GET();
  String payload = "";
  
  if (code >= 200 && code < 300) {
    payload = http.getString();
    Serial.println("Fetched cards from DB");
  } else {
    Serial.print("Error fetching cards: ");
    Serial.println(code);
  }
  
  http.end();
  return payload;
}
#endif
