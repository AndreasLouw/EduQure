#ifndef SECRETS_H
#define SECRETS_H

#include <Arduino.h>

// WiFi Configuration
const char* WIFI_SSID = "";
const char* WIFI_PASS = "";

// Supabase Configuration
// Supabase Configuration
const char* SUPABASE_URL = ""; 
const char* SUPABASE_KEY = "";
const char* LOCK_ID = "lock-1";

// Authorized UIDs are now managed dynamically via card_manager.h and Supabase
// const String AUTHORIZED_UIDS[] = { ... };
// const int NUM_AUTHORIZED_UIDS = ...;

#endif
