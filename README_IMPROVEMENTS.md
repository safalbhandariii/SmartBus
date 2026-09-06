# SmartBus v3 — Improvements

## What changed

### Driver / Admin separation
- Passenger registration is now a **Driver-only** operation.
- The public Role Picker no longer exposes passenger registration.
- A logged-in driver gets a **REGISTER NEW PASSENGER** action on the Driver Dashboard.
- Registration pages redirect to Driver Login if no driver is authenticated.

### Registration validation
- eSewa/login ID must be unique.
- Generated SmartBus Passenger IDs are checked for collisions.
- Passenger passwords must contain at least 6 characters.
- Registration captures liveness before face capture.

### Persistent transaction history
Successful exits are stored in `transactions.json` with:
- passenger ID/name
- distance
- fare
- payment method (Wallet / eSewa / Credit)
- driver
- bus ID
- timestamp

This makes the history available after restarting the app and lets Super Admin calculate today's revenue.

### Payment safety
- Passenger quick-top-up buttons now launch eSewa instead of creating free wallet credit.
- Fixed the credit-payment exit path so it no longer passes an unsupported argument to `finish_exit()`.
- eSewa remains available as a payment choice even when the wallet can cover the fare.

### File-write safety
JSON writes use a temporary file + `os.replace()` to avoid leaving a half-written database if the process is interrupted.
The driver revenue update also reloads the latest `drivers.json` before incrementing revenue, reducing stale-write conflicts between the Driver and Super Admin apps.

### Super Admin
- Revenue refresh now shows **Today's Revenue** and **All-Time Revenue**.
- Driver list is reloaded from disk on refresh.
- Added **Reset Passenger Password**.
- Master password can optionally be supplied through the `SMARTBUS_ADMIN_PASSWORD` environment variable; `super123` remains the local-project fallback.

## Running

Driver / passenger application:
```text
py mainGUI.py
```

Super Admin:
```text
py superadmin_app.py
```

Both applications must be run from the `SmartBus_v3` directory so their JSON files and model files resolve correctly.

## Important project limitation

This project still uses JSON files rather than a real database. Atomic writes reduce corruption risk, but JSON is not a full multi-user database solution. For a larger deployment, SQLite/PostgreSQL with transactions would be the next architectural upgrade.
