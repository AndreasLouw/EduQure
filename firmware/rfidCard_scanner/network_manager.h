#ifndef NETWORK_MANAGER_H
#define NETWORK_MANAGER_H

#include <WiFi.h>
#include <HTTPClient.h>
#include "secrets.h"
#include "time.h"
#include "debug.h"

// Time settings for South Africa (UTC+2)
const char* ntpServer = "pool.ntp.org";
const long  gmtOffset_sec = 7200;
const int   daylightOffset_sec = 0;

void setupWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 15000) {
    delay(500);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi Connected!");
    DBG_VAL("IP Address: ", WiFi.localIP());

    configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
    DBG("Waiting for time sync...");
    start = millis();
    struct tm timeinfo;
    while (!getLocalTime(&timeinfo) && millis() - start < 5000) {
      DBG(".");
      delay(100);
    }
    DBG("Time synced.");
  } else {
    WiFi.disconnect(true);  // Power down radio — stops background retries that cause power spikes
    Serial.println("\nWiFi Connection Failed (Continuing in Offline Mode)");
  }
}

String getISOTime() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    Serial.println("ERROR: Failed to obtain time");
    return "";
  }

  char timeStringBuff[30];
  strftime(timeStringBuff, sizeof(timeStringBuff), "%Y-%m-%dT%H:%M:%S", &timeinfo);
  return String(timeStringBuff) + "+02:00";
}

// Returns HTTP response code, or -1 if not connected / network error.
// 2xx = success, 4xx = permanent rejection (don't retry), 5xx/-1 = temporary (retry later).
int sendLogToSupabase(String uid, bool accessGranted, String timestamp) {
  if (WiFi.status() != WL_CONNECTED) {
    return -1;
  }

  HTTPClient http;

  String baseUrl = String(SUPABASE_URL);
  if (baseUrl.endsWith("/")) baseUrl.remove(baseUrl.length() - 1);

  String url;
  String payload;

  if (accessGranted) {
    url = baseUrl + "/rest/v1/access_logs";
    payload = "{\"card_uid\":\"" + uid + "\", \"lock\":\"" + String(LOCK_ID) + "\", \"status\":true";
    if (timestamp.length() > 0) payload += ", \"created_at\":\"" + timestamp + "\"";
    payload += "}";
  } else {
    url = baseUrl + "/rest/v1/unidentified_cards";
    payload = "{\"card_uid\":\"" + uid + "\", \"lock\":\"" + String(LOCK_ID) + "\"";
    if (timestamp.length() > 0) payload += ", \"created_at\":\"" + timestamp + "\"";
    payload += "}";
  }

  DBG_VAL("POST ", url);
  DBG_VAL("Payload: ", payload);

  http.begin(url);
  http.setConnectTimeout(5000);
  http.setTimeout(8000);
  http.addHeader("apikey", SUPABASE_KEY);
  http.addHeader("Authorization", "Bearer " + String(SUPABASE_KEY));
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Prefer", "return=minimal");

  int code = http.POST(payload);
  http.end();

  if (code >= 200 && code < 300) {
    Serial.println("Sync OK: " + String(code));
  } else {
    Serial.println("Sync Error: " + String(code));
  }

  return code;
}

String fetchCardsJSON() {
  if (WiFi.status() != WL_CONNECTED) return "";

  HTTPClient http;
  String baseUrl = String(SUPABASE_URL);
  if (baseUrl.endsWith("/")) baseUrl.remove(baseUrl.length() - 1);

  String url = baseUrl + "/rest/v1/persons?select=card_uid";

  http.begin(url);
  http.setConnectTimeout(2000);
  http.setTimeout(2000);
  http.addHeader("apikey", SUPABASE_KEY);
  http.addHeader("Authorization", "Bearer " + String(SUPABASE_KEY));

  int code = http.GET();
  String payload = "";

  if (code >= 200 && code < 300) {
    payload = http.getString();
    DBG("Cards fetched from DB");
  } else {
    Serial.println("ERROR fetching cards: " + String(code));
  }

  http.end();
  return payload;
}

#endif
