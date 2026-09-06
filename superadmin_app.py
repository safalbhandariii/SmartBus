"""
superadmin_app.py
-------------------
Standalone Super Admin console for SmartBus — intentionally a SEPARATE
application from mainGUI.py.

Why separate:
  - The master password and driver-account-creation logic never load
    into the same process a driver or passenger ever runs.
  - Regular users (drivers, passengers) have no way to discover this
    tool even exists — it isn't listed anywhere in mainGUI.py's Role
    Picker or navigation.
  - Only whoever has this file (and the master password) can manage
    driver accounts / see cross-bus revenue.

Run it directly:
    py superadmin_app.py

Shares `drivers.json` on disk with mainGUI.py (same folder) — driver
accounts created here are immediately usable for Driver Login in the
main app, and revenue numbers update live as drivers process fares
over there.
"""

import tkinter as tk
from tkinter import messagebox
import json
import os
import hashlib
from datetime import datetime
import tempfile

# ============================================================
# MASTER PASSWORD
# (change this before sharing/deploying the project)
# ============================================================

MASTER_SUPERADMIN_PASSWORD = os.environ.get("SMARTBUS_ADMIN_PASSWORD", "super123")

# ============================================================
# UI COLORS (matches mainGUI.py's palette for visual consistency)
# ============================================================

BG = "#F4F7FB"
CARD = "#FFFFFF"
NAVY = "#0F2747"
DARK = "#334155"
DARK_HOVER = "#1E293B"
GREEN = "#16A34A"
RED = "#DC2626"
TEXT = "#1E293B"
MUTED = "#64748B"
BORDER = "#E2E8F0"


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def atomic_save_json(path, data):
    directory = os.path.dirname(path) or "."
    fd, temp_path = tempfile.mkstemp(prefix=".smartbus_", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def load_drivers():
    if not os.path.exists("drivers.json"):
        atomic_save_json("drivers.json", {})
    try:
        with open("drivers.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}


def save_drivers():
    atomic_save_json("drivers.json", drivers)


def load_transactions():
    if not os.path.exists("transactions.json"):
        return []
    try:
        with open("transactions.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return []


drivers = load_drivers()
transactions = load_transactions()


def make_button(parent, text, command, bg, active_bg, width=18, height=2, font_size=11):
    button = tk.Button(
        parent, text=text, command=command,
        font=("Segoe UI", font_size, "bold"),
        width=width, height=height, bg=bg, fg="white",
        activebackground=active_bg, activeforeground="white",
        relief="flat", bd=0, cursor="hand2", highlightthickness=0
    )
    button.bind("<Enter>", lambda e: button.configure(bg=active_bg))
    button.bind("<Leave>", lambda e: button.configure(bg=bg))
    return button


def make_section_title(parent, icon, title):
    frame = tk.Frame(parent, bg=BG)
    tk.Label(frame, text=icon, font=("Segoe UI Emoji", 17), bg=BG, fg=NAVY).pack(side="left")
    tk.Label(frame, text=title, font=("Segoe UI", 14, "bold"), bg=BG, fg=NAVY).pack(side="left", padx=(8, 0))
    return frame


# ============================================================
# WINDOW
# ============================================================

window = tk.Tk()
window.title("SmartBus — Super Admin Console")
window.geometry("760x640")
window.minsize(600, 500)
window.configure(bg=BG)

container = tk.Frame(window, bg=BG)
container.pack(fill="both", expand=True)
container.grid_rowconfigure(0, weight=1)
container.grid_columnconfigure(0, weight=1)

pages = {}


def register_page(name, frame):
    pages[name] = frame
    frame.grid(row=0, column=0, sticky="nsew")


def show_page(name):
    pages[name].tkraise()


# ============================================================
# PAGE: LOGIN
# ============================================================

def build_login():
    frame = tk.Frame(container, bg=BG)

    card = tk.Frame(frame, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    card.place(relx=0.5, rely=0.5, anchor="center", width=380, height=260)

    tk.Label(card, text="🛡️ Super Admin Console", font=("Segoe UI", 16, "bold"), bg=CARD, fg=NAVY).pack(pady=(30, 6))
    tk.Label(card, text="Master password required.", font=("Segoe UI", 9), bg=CARD, fg=MUTED).pack(pady=(0, 20))

    password_entry = tk.Entry(card, font=("Segoe UI", 11), show="•")
    password_entry.pack(fill="x", padx=40, pady=(2, 16))
    password_entry.focus()

    error_label = tk.Label(card, text="", font=("Segoe UI", 9), bg=CARD, fg=RED)
    error_label.pack()

    def try_login(event=None):
        if password_entry.get() != MASTER_SUPERADMIN_PASSWORD:
            error_label.config(text="Incorrect master password.")
            return

        error_label.config(text="")
        password_entry.delete(0, tk.END)
        refresh_driver_list()
        show_page("dashboard")

    password_entry.bind("<Return>", try_login)
    make_button(card, "LOG IN", try_login, DARK, DARK_HOVER, width=20, height=1, font_size=10).pack(pady=(0, 8))

    return frame


# ============================================================
# PAGE: DASHBOARD
# ============================================================

driver_list_label = None


def refresh_driver_list():
    # Reload so changes made by the Driver app are visible after Refresh.
    latest = load_drivers()
    drivers.clear()
    drivers.update(latest)
    transactions.clear()
    transactions.extend(load_transactions())

    if not drivers:
        driver_list_label.config(text="No drivers registered yet.")
        return

    today = datetime.now().date()
    today_revenue = sum(
        float(t.get("fare", 0))
        for t in transactions
        if t.get("timestamp", "")[:10] == today.isoformat()
    )
    all_time = sum(float(data.get("revenue", 0)) for data in drivers.values())

    text = (
        f"📅 Today's Revenue: Rs. {today_revenue:.2f}    •    "
        f"💰 All-Time Revenue: Rs. {all_time:.2f}\n\n"
    )
    for username, data in drivers.items():
        text += (
            f"🚌 {data.get('bus_id', 'Unassigned')}   •   "
            f"Driver: {username}   •   Revenue: Rs. {float(data.get('revenue', 0)):.2f}\n"
        )

    driver_list_label.config(text=text.rstrip())


def build_dashboard():
    global driver_list_label

    frame = tk.Frame(container, bg=BG)
    inner = tk.Frame(frame, bg=BG)
    inner.pack(fill="both", expand=True, padx=40, pady=30)

    tk.Label(inner, text="🛡️ Super Admin Dashboard", font=("Segoe UI", 20, "bold"), bg=BG, fg=NAVY).pack(anchor="w")
    tk.Label(inner, text="Manage driver accounts, recover passenger access and monitor revenue across all buses.",
             font=("Segoe UI", 10), bg=BG, fg=MUTED).pack(anchor="w", pady=(2, 20))

    # ---- Revenue per bus ----
    make_section_title(inner, "💰", "Revenue by Bus").pack(anchor="w", pady=(0, 8), fill="x")

    rev_card = tk.Frame(inner, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    rev_card.pack(fill="x", pady=(0, 24))

    driver_list_label = tk.Label(
        rev_card, text="No drivers registered yet.",
        font=("Segoe UI", 10), bg=CARD, fg=TEXT, justify="left", anchor="w"
    )
    driver_list_label.pack(fill="x", padx=20, pady=15)

    refresh_btn = make_button(inner, "↻  Refresh", refresh_driver_list, "#E8EEF7", "#DCE6F3", width=14, height=1, font_size=9)
    refresh_btn.configure(fg=NAVY, activeforeground=NAVY)
    refresh_btn.pack(anchor="w", pady=(0, 20))

    # ---- Create driver account ----
    make_section_title(inner, "➕", "Create Driver Account").pack(anchor="w", pady=(0, 8), fill="x")

    create_card = tk.Frame(inner, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    create_card.pack(fill="x", pady=(0, 24))

    form = tk.Frame(create_card, bg=CARD)
    form.pack(fill="x", padx=18, pady=15)

    tk.Label(form, text="Username", font=("Segoe UI", 9, "bold"), bg=CARD, fg=TEXT).grid(row=0, column=0, sticky="w")
    new_username_entry = tk.Entry(form, font=("Segoe UI", 10), width=18)
    new_username_entry.grid(row=1, column=0, sticky="w", padx=(0, 12), pady=(0, 10))

    tk.Label(form, text="Password", font=("Segoe UI", 9, "bold"), bg=CARD, fg=TEXT).grid(row=0, column=1, sticky="w")
    new_password_entry = tk.Entry(form, font=("Segoe UI", 10), width=18, show="•")
    new_password_entry.grid(row=1, column=1, sticky="w", padx=(0, 12), pady=(0, 10))

    tk.Label(form, text="Bus ID", font=("Segoe UI", 9, "bold"), bg=CARD, fg=TEXT).grid(row=0, column=2, sticky="w")
    new_busid_entry = tk.Entry(form, font=("Segoe UI", 10), width=18)
    new_busid_entry.grid(row=1, column=2, sticky="w", pady=(0, 10))

    create_status = tk.Label(form, text="", font=("Segoe UI", 9), bg=CARD, fg=RED)
    create_status.grid(row=2, column=0, columnspan=3, sticky="w")

    def create_driver():
        username = new_username_entry.get().strip()
        password = new_password_entry.get()
        bus_id = new_busid_entry.get().strip()

        if not username or not password or not bus_id:
            create_status.config(text="Fill in all fields.", fg=RED)
            return

        if username in drivers:
            create_status.config(text="That username already exists.", fg=RED)
            return

        drivers[username] = {
            "password_hash": hash_password(password),
            "bus_id": bus_id,
            "revenue": 0.0
        }
        save_drivers()

        create_status.config(text=f"Driver '{username}' created.", fg=GREEN)
        new_username_entry.delete(0, tk.END)
        new_password_entry.delete(0, tk.END)
        new_busid_entry.delete(0, tk.END)
        refresh_driver_list()

    make_button(form, "CREATE DRIVER", create_driver, DARK, DARK_HOVER, width=20, height=1, font_size=10).grid(row=1, column=3, padx=(12, 0))

    # ---- Remove driver account ----
    make_section_title(inner, "🗑️", "Remove Driver Account").pack(anchor="w", pady=(0, 8), fill="x")

    remove_card = tk.Frame(inner, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    remove_card.pack(fill="x", pady=(0, 24))

    remove_form = tk.Frame(remove_card, bg=CARD)
    remove_form.pack(fill="x", padx=18, pady=15)

    tk.Label(remove_form, text="Username to remove", font=("Segoe UI", 9, "bold"), bg=CARD, fg=TEXT).grid(row=0, column=0, sticky="w")
    remove_username_entry = tk.Entry(remove_form, font=("Segoe UI", 10), width=18)
    remove_username_entry.grid(row=1, column=0, sticky="w", padx=(0, 12))

    remove_status = tk.Label(remove_form, text="", font=("Segoe UI", 9), bg=CARD, fg=RED)
    remove_status.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def remove_driver():
        username = remove_username_entry.get().strip()
        if not username:
            remove_status.config(text="Enter a username.", fg=RED)
            return
        if username not in drivers:
            remove_status.config(text="No such driver account.", fg=RED)
            return

        confirmed = messagebox.askyesno(
            "Confirm removal",
            f"Remove driver '{username}'? This cannot be undone.\n"
            f"(The driver account is removed; existing transaction records remain.)"
        )
        if not confirmed:
            return

        del drivers[username]
        save_drivers()
        remove_status.config(text=f"Driver '{username}' removed.", fg=GREEN)
        remove_username_entry.delete(0, tk.END)
        refresh_driver_list()

    make_button(remove_form, "REMOVE", remove_driver, RED, "#B91C1C", width=14, height=1, font_size=10).grid(row=1, column=1, sticky="w")

    # ---- Reset passenger password ----
    make_section_title(inner, "🔑", "Reset Passenger Password").pack(anchor="w", pady=(0, 8), fill="x")

    reset_card = tk.Frame(inner, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    reset_card.pack(fill="x", pady=(0, 24))
    reset_form = tk.Frame(reset_card, bg=CARD)
    reset_form.pack(fill="x", padx=18, pady=15)

    tk.Label(reset_form, text="Passenger ID", font=("Segoe UI", 9, "bold"), bg=CARD, fg=TEXT).grid(row=0, column=0, sticky="w")
    passenger_id_entry = tk.Entry(reset_form, font=("Segoe UI", 10), width=18)
    passenger_id_entry.grid(row=1, column=0, padx=(0, 12), pady=(0, 8))

    tk.Label(reset_form, text="New Password", font=("Segoe UI", 9, "bold"), bg=CARD, fg=TEXT).grid(row=0, column=1, sticky="w")
    passenger_password_entry = tk.Entry(reset_form, font=("Segoe UI", 10), width=18, show="•")
    passenger_password_entry.grid(row=1, column=1, padx=(0, 12), pady=(0, 8))

    reset_status = tk.Label(reset_form, text="", font=("Segoe UI", 9), bg=CARD, fg=RED)
    reset_status.grid(row=2, column=0, columnspan=3, sticky="w")

    def reset_passenger_password():
        pid = passenger_id_entry.get().strip()
        new_password = passenger_password_entry.get()
        if not pid or not new_password:
            reset_status.config(text="Fill in both fields.", fg=RED)
            return
        if len(new_password) < 6:
            reset_status.config(text="Password must contain at least 6 characters.", fg=RED)
            return

        path = "passengers.json"
        try:
            with open(path, "r", encoding="utf-8") as file:
                passenger_data = json.load(file)
        except (OSError, json.JSONDecodeError):
            reset_status.config(text="Could not read passenger database.", fg=RED)
            return

        if pid not in passenger_data:
            reset_status.config(text="Passenger ID not found.", fg=RED)
            return

        passenger_data[pid]["password_hash"] = hash_password(new_password)
        atomic_save_json(path, passenger_data)
        passenger_password_entry.delete(0, tk.END)
        reset_status.config(text=f"Password reset for passenger {pid}.", fg=GREEN)

    make_button(reset_form, "RESET PASSWORD", reset_passenger_password, DARK, DARK_HOVER, width=18, height=1, font_size=9).grid(row=1, column=2, padx=(0, 0))

    make_button(inner, "🔒  Log Out", lambda: show_page("login"), "#E8EEF7", "#DCE6F3", width=16, height=1, font_size=9).configure(fg=NAVY, activeforeground=NAVY)

    return frame


# ============================================================
# BUILD + RUN
# ============================================================

register_page("login", build_login())
register_page("dashboard", build_dashboard())
show_page("login")

window.mainloop()
