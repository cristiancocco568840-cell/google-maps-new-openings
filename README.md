# Google Maps New Openings Radar

## Funzioni
- prima scansione = baseline;
- dalle scansioni successive: evidenzia solo Place ID mai visti;
- include `FUTURE_OPENING` e `openingDate`;
- telefono, sito e link Maps quando disponibili;
- export Excel con telefono formattato come **testo** e senza +39;
- scansione geografica a micro-celle;
- autopilot giornaliero opzionale;
- alert Telegram/email opzionali.

## Google Cloud
Abilita **Places API (New)**, crea una API key e imposta `GOOGLE_MAPS_API_KEY`.

## Render
1. Carica la cartella in GitHub.
2. Render > New > Blueprint.
3. Seleziona il repository.
4. Inserisci `GOOGLE_MAPS_API_KEY`.
5. Avvia il servizio.

Il database è salvato in `/var/data/places.db` su persistent disk.

## Prima scansione
Esegui manualmente Milano una volta. È la baseline e non genera falsi "nuovi".

## Autopilot
Dopo la baseline imposta su Render:
- `AUTO_SCAN_ENABLED=true`
- `AUTO_SCAN_TIMEZONE=Europe/Rome`
- `AUTO_SCAN_HOUR=7`
- `AUTO_SCAN_MINUTE=30`
- `AUTO_SCAN_PRESET=Milano`

Lo scan parte ogni giorno alle 07:30 ora italiana finché il web service resta attivo.

### Perché non un Render Cron Job?
Render documenta che i Cron Job non possono accedere al persistent disk di un altro servizio. Per questo l'MVP usa uno scheduler interno e `gunicorn --workers 1` per evitare scansioni duplicate. Per una versione più robusta: Postgres + Render Cron Job.

## Alert Telegram
Imposta:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `PUBLIC_BASE_URL=https://tuo-servizio.onrender.com`

Il radar invia un messaggio solo quando trova nuove attività/aperture future.

## Limite strutturale
Nearby Search restituisce al massimo 20 risultati per richiesta. La griglia e i piccoli batch di categorie aumentano la copertura, ma non esiste garanzia matematica del 100% di tutte le schede Maps.
