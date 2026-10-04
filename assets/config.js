/* Actually Free — site configuration.
   GOATCOUNTER_CODE: your Goatcounter site code (the subdomain part of your
   Goatcounter URL). Free signup at https://www.goatcounter.com — no API key
   needed. Until this is set, analytics are skipped silently.

   Feedback reports ("doesn't work" / "broke a promise" / corrections /
   app suggestions) go to ntfy.sh — free tier, no account, no backend. The
   topic is NOT stored here: generate.py reads it from the AF_NTFY_TOPIC
   environment variable or ~/.config/actually-free/ntfy-topic, XOR-obfuscates
   it with a fresh random key on every build, and embeds only base64 blobs in
   the pages. Subscribe to the topic in the ntfy app (Android) or at ntfy.sh
   to receive reports; the free tier keeps messages ~12 hours. */
window.AF_CONFIG = {
  GOATCOUNTER_CODE: "actually-free"
};
