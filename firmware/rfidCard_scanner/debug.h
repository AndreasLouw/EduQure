#ifndef DEBUG_H
#define DEBUG_H

// ── Debug mode ─────────────────────────────────────────────────────────────
// Set to 1 for verbose serial output (UIDs, HTTP details, queue status).
// Set to 0 for production — only critical events are printed.
#define DEBUG_MODE 1
// ───────────────────────────────────────────────────────────────────────────

#if DEBUG_MODE
  #define DBG(msg)            Serial.println(msg)
  #define DBG_VAL(label, val) do { Serial.print(label); Serial.println(val); } while(0)
#else
  #define DBG(msg)
  #define DBG_VAL(label, val)
#endif

#endif
