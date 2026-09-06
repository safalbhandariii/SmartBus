# SmartBus

Face-recognition boarding, distance-based fares, and a digital wallet — a cashless fare system for Nepal's public buses.

## Team Information

**Team Name:** [The Cipher Triad]

**Team Members:**

| Name | Email | GitHub Username |
|---|---|---|
| Pratik Dhakal | dhalakpratik07@gmail.com | @pratikdhakal1 |
| Sushan Shrestha| sushanstha2063@gmail.com | @sushanstha-glitch |
| Safal Bhandari | safalbhandari06@gmail.com | @safalbhandariii |

## Project Details

**Project Title:** SmartBus — Automated Fare Collection & Wallet System

**Category:** [x] FinTech GovTech CivicTech &nbsp; [ ] EdTech &nbsp; [ ] E-Governance &nbsp; [ ] IoT &nbsp; [ ] Open Innovation

**Problem Statement:**
Nepal's public buses are still run on cash and guesswork: conductors and drivers earn a cut of whatever they collect, which fuels the unsafe "penny war" for passengers on the road. Fares are undocumented, so operators can't audit route revenue or resolve disputes, and legally mandated student/senior discounts can't be verified on a crowded bus. Nepal has tried to fix this before — Sajha Yatayat's 2017 smart travel cards, and similar pilots in Pokhara and Bharatpur — but adoption stayed low because recharging was inconvenient and there was no government mandate.

**Solution Overview:**
SmartBus replaces the fare card with something every passenger already has: their face. A passenger registers once (face photo + password); after that, a camera at the door recognizes them on boarding and exit, the distance travelled is tracked automatically, and the fare is calculated and deducted from an in-app wallet — with an eSewa top-up flow for when the balance runs low. The system is split into three cooperating apps: a **Passenger Portal** (self-registration, wallet balance/history, eSewa top-up), a **Driver Dashboard** (face-scan boarding/exit, new-passenger registration, live bus simulation, today's revenue), and a **Super Admin App** (driver account management, passenger password resets, revenue reporting). All three read and write the same JSON data store, kept consistent through atomic file writes.

## Technical Stack

| Layer | Technology |
|---|---|
| Application / GUI | Python 3, Tkinter, Pillow (PIL) for image rendering |
| Computer Vision | OpenCV (`opencv-contrib-python`) — Haar cascade face/eye detection + LBPH face recognizer |
| Data Store | Flat JSON files (`passengers.json`, `drivers.json`, `transactions.json`) with atomic (`temp file` + `os.replace()`) writes |
| Payments | eSewa ePay v2 (HMAC-SHA256 signed sandbox flow) via `esewa_payment.py`, with a local `http.server` callback listener for verification |
| Security | `hashlib` SHA-256 password hashing for passengers and drivers |

## Installation & Setup

### Prerequisites
- Python 3.10+
- A working webcam (for live face scanning/registration)
- `pip` for installing dependencies

### Steps

```bash
# Clone the repository
git clone [https://github.com/Nepalaya-IT-Club/](https://github.com/Nepalaya-IT-Club/)<team-repo-name>.git

# Navigate to the project folder
cd SmartBus

# Install dependencies
pip install opencv-contrib-python numpy pillow

# Run from inside the project folder so JSON/model files resolve correctly

# Start the Driver / Passenger application
python mainGUI.py

# In a separate terminal, start the Super Admin app
python superadmin_app.py
```

Both apps are desktop Tkinter windows (not a web server) — running either script opens its GUI directly.

### Environment Variables (if applicable)

This project reads configuration from OS environment variables rather than a `.env` file. Setting the variable below is optional — it falls back to a local default if unset.

```bash
export SMARTBUS_ADMIN_PASSWORD="your-chosen-password"   # macOS/Linux
set SMARTBUS_ADMIN_PASSWORD=your-chosen-password         # Windows
```

| Variable | Required | Description |
|---|---|---|
| SMARTBUS_ADMIN_PASSWORD | No | Overrides the Super Admin master password (defaults to `super123` for local/demo use) |

eSewa is wired to the public UAT sandbox (test merchant code `EPAYTEST`) directly in `esewa_payment.py` — no keys need to be supplied to run the demo.

## Demo Credentials (if applicable)

| Role | Access |
|---|---|
| Super Admin | Launch `superadmin_app.py` → password `super123` (or your `SMARTBUS_ADMIN_PASSWORD` value) |
| Driver | Sample accounts (`driver1`, `Driver 2`, `Driver 3`) exist in `drivers.json`; create a fresh driver with a known password from the Super Admin app, or reset via Super Admin |
| Passenger | Register a new passenger from the Driver Dashboard's **Register New Passenger** flow — this captures a live face photo and sets a password you choose |

## Demo Flow

1. Start `superadmin_app.py`, log in, and create a driver account (or use an existing one after resetting its password).
2. Start `mainGUI.py`, choose **Driver Login**, and sign in with that driver account.
3. From the Driver Dashboard, select **Register New Passenger** and capture a new passenger's face and details.
4. Use **Scan / Board** to recognize and board that passenger, then advance the simulated bus distance.
5. Use **Scan / Exit** to end the ride — watch the fare get calculated and deducted from the wallet (or trigger an eSewa top-up if the balance is too low).
6. Switch back to the Super Admin app and refresh **Revenue** to see the completed trip reflected in Today's/All-Time Revenue.

## Screenshots / Demo

[Add screenshots or a link to a short demo video here.]

## Project Structure

```
SmartBus/
├── mainGUI.py                       # Main Driver + Passenger Tkinter application (primary entry point)
├── superadmin_app.py                # Super Admin Tkinter application (second entry point)
├── esewa_payment.py                 # eSewa ePay v2 signing, redirect, and callback verification
├── liveness.py                      # Liveness check (stable-frame presence detection) before face match
├── camera.py                        # Webcam capture helper
├── recognize.py                     # LBPH face recognition helper
├── register.py / register_passenger.py / mainRegister.py   # Passenger registration + face capture flows
├── train.py                         # (Re)trains the LBPH recognizer from registered face photos
├── fare.py                          # Fare calculation logic
├── trip.py                          # Trip/board-exit state helpers
├── bus_simulator.py                 # Simulated bus distance progression
├── passengers.py                    # Passenger data access helpers
├── passengers.json                  # Passenger records (profile, wallet balance, hashed password)
├── drivers.json                     # Driver accounts (hashed password, bus ID, revenue)
├── transactions.json                # Persisted ride/payment history
├── trainer.yml                      # Trained LBPH face-recognition model
├── haarcascade_frontalface_default.xml / haarcascade_eye.xml   # OpenCV Haar cascade models
├── assets/                          # Logo and static images
├── faces/                           # Captured passenger face photos
├── README_IMPROVEMENTS.md           # Changelog and known limitations
└── README.md
```

## License

This project was built for **CodeRush 2026**, organized by Nepalaya IT Club.
