import tkinter as tk
import cv2
import json
import os
import numpy as np
import hashlib
from datetime import datetime
import tempfile
import esewa_payment
import liveness
from tkinter import messagebox
from PIL import Image, ImageTk, ImageOps

# ============================================================
# MODERN UI COLORS
# ============================================================

BG = "#F4F7FB"
CARD = "#FFFFFF"
NAVY = "#0F2747"
HEADER_BG = "#111827"
BLUE = "#2563EB"
BLUE_DARK = "#1D4ED8"
GREEN = "#16A34A"
GREEN_DARK = "#15803D"
RED = "#DC2626"
RED_DARK = "#B91C1C"
AMBER = "#D97706"
TEXT = "#1E293B"
MUTED = "#64748B"
BORDER = "#E2E8F0"
LIGHT_BLUE = "#EAF2FF"
LIGHT_GREEN = "#EAF8EF"
LIGHT_RED = "#FEF0F0"
LIGHT_AMBER = "#FFF7E8"


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ============================================================
# DATA FILES
# ============================================================

def atomic_save_json(path, data):
    """Write JSON safely so a second process cannot observe a half-written file."""
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


def load_json(path, default):
    if not os.path.exists(path):
        atomic_save_json(path, default)
        return default
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return default


passengers = load_json("passengers.json", {})


def save_passengers():
    atomic_save_json("passengers.json", passengers)


def load_drivers():
    return load_json("drivers.json", {})


def save_drivers():
    atomic_save_json("drivers.json", drivers)


def load_transactions():
    return load_json("transactions.json", [])


def save_transactions():
    atomic_save_json("transactions.json", transaction_history)


drivers = load_drivers()

# ============================================================
# RUNTIME STATE
# ============================================================

distance = 0.0
speed = 30

onboard_passengers = {}
transaction_history = load_transactions()

current_driver = None   # username of the driver currently logged in


# ============================================================
# FACE RECOGNITION
# ============================================================

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("trainer.yml")

face_detector = cv2.CascadeClassifier(
    "haarcascade_frontalface_default.xml"
)

eye_cascade = cv2.CascadeClassifier(
    "haarcascade_eye.xml"
)


def retrain_recognizer():
    faces_list = []
    ids_list = []
    for filename in os.listdir("faces"):
        if not filename.endswith(".jpg"):
            continue
        image = cv2.imread(os.path.join("faces", filename), cv2.IMREAD_GRAYSCALE)
        if image is None:
            continue
        try:
            face_id = int(filename.split(".")[0])
        except ValueError:
            continue
        faces_list.append(image)
        ids_list.append(face_id)
    if not faces_list:
        return False
    recognizer.train(faces_list, np.array(ids_list))
    recognizer.write("trainer.yml")
    return True


def scan_face():

    camera = cv2.VideoCapture(0)

    # ---- Liveness check FIRST: reject photo/video/screen spoofing ----
    is_live, reason = liveness.run_liveness_check(camera, face_detector, eye_cascade)

    if not is_live:
        camera.release()
        cv2.destroyAllWindows()
        messagebox.showwarning("Liveness Check Failed", reason)
        return None

    # ---- Liveness passed (possibly with an advisory warning) ----
    if "flagged" in reason.lower():
        messagebox.showinfo("Liveness Notice", reason)

    detected_id = None

    while True:

        success, frame = camera.read()
        if not success:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face_detector.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50)
        )

        for (x, y, w, h) in faces:

            face_id, confidence = recognizer.predict(gray[y:y+h, x:x+w])

            if confidence < 70:
                detected_id = face_id
                text = f"Passenger {face_id}"
            else:
                text = "Unknown"

            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        cv2.imshow("SmartBus - Face Scanner", frame)

        key = cv2.waitKey(1) & 0xFF

        if detected_id is not None:
            break
        if key == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

    return detected_id


def generate_next_id():
    if passengers:
        existing_ids = [int(pid) for pid in passengers.keys() if pid.isdigit()]
        if existing_ids:
            return str(max(existing_ids) + 1)
    return "1"


# ============================================================
# HELPER WIDGETS
# ============================================================

def make_button(parent, text, command, bg, active_bg,
                width=18, height=2, font_size=11):
    button = tk.Button(
        parent, text=text, command=command,
        font=("Segoe UI", font_size, "bold"),
        width=width, height=height, bg=bg, fg="white",
        activebackground=active_bg, activeforeground="white",
        relief="flat", bd=0, cursor="hand2", highlightthickness=0
    )

    def on_enter(event):
        button.configure(bg=active_bg)

    def on_leave(event):
        button.configure(bg=bg)

    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)

    return button


def make_section_title(parent, icon, title, subtitle=None):
    frame = tk.Frame(parent, bg=BG)

    top = tk.Frame(frame, bg=BG)
    top.pack(fill="x")

    tk.Label(top, text=icon, font=("Segoe UI Emoji", 17), bg=BG, fg=NAVY).pack(side="left")
    tk.Label(top, text=title, font=("Segoe UI", 14, "bold"), bg=BG, fg=NAVY).pack(side="left", padx=(8, 0))

    if subtitle:
        tk.Label(frame, text=subtitle, font=("Segoe UI", 9), bg=BG, fg=MUTED).pack(anchor="w", padx=(32, 0), pady=(1, 0))

    return frame


def make_portal_nav_bar(parent, current_page_name):
    """
    A persistent, thin top strip shown on every portal page, letting the
    user jump directly to any other portal without logging out first.
    `current_page_name` is dimmed/disabled so the active portal isn't
    shown as a clickable link to itself.
    """
    bar = tk.Frame(parent, bg="#1E293B", height=36)
    bar.pack(fill="x", side="top")
    bar.pack_propagate(False)

    tk.Label(bar, text="🚌 SmartBus", font=("Segoe UI", 9, "bold"), bg="#1E293B", fg="white").pack(side="left", padx=(14, 18))

    portal_links = [
        ("🏠 Home", "role_picker"),
        ("🚍 Driver", "driver_login"),
        ("📝 Register", "registration"),
        ("👤 Passenger", "user_login"),
    ]

    for label, page_name in portal_links:
        is_current = (page_name == current_page_name)
        link = tk.Label(
            bar,
            text=label,
            font=("Segoe UI", 9, "bold" if is_current else "normal"),
            bg="#1E293B",
            fg="#64748B" if is_current else "#CBD5E1",
            cursor="arrow" if is_current else "hand2",
            padx=10
        )
        link.pack(side="left")

        if not is_current:
            def make_handler(target=page_name):
                if target == "registration":
                    return lambda event: open_driver_registration()
                return lambda event: show_page(target)

            handler = make_handler()
            link.bind("<Button-1>", handler)
            link.bind("<Enter>", lambda e, w=link: w.configure(fg="white"))
            link.bind("<Leave>", lambda e, w=link: w.configure(fg="#CBD5E1"))

    return bar


# ============================================================
# MAIN WINDOW + PAGE CONTAINER
# ============================================================

window = tk.Tk()
window.title("SmartBus - Automated Fare Collection")
window.geometry("980x760")
window.minsize(760, 600)
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
# PAGE: ROLE PICKER
# ============================================================

def build_role_picker():
    frame = tk.Frame(container, bg=BG)

    # Hero header
    hero = tk.Frame(frame, bg=HEADER_BG, height=170)
    hero.pack(fill="x")
    hero.pack_propagate(False)

    tk.Label(
        hero, text="🚌  SmartBus", font=("Segoe UI", 30, "bold"),
        bg=HEADER_BG, fg="white"
    ).pack(pady=(32, 2))
    tk.Label(
        hero, text="Smart • Simple • Cashless Public Transport",
        font=("Segoe UI", 11), bg=HEADER_BG, fg="#CBD5E1"
    ).pack()

    body = tk.Frame(frame, bg=BG)
    body.pack(fill="both", expand=True, padx=55, pady=28)

    tk.Label(
        body, text="Welcome to SmartBus", font=("Segoe UI", 20, "bold"),
        bg=BG, fg=TEXT
    ).pack()
    tk.Label(
        body, text="Choose what you want to do", font=("Segoe UI", 10),
        bg=BG, fg=MUTED
    ).pack(pady=(3, 22))

    cards = tk.Frame(body, bg=BG)
    cards.pack(fill="x")
    cards.columnconfigure(0, weight=1)
    cards.columnconfigure(1, weight=1)

    def portal_card(column, icon, title, subtitle, button_text, command, color):
        card = tk.Frame(cards, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 9, 9 if column == 0 else 0))

        tk.Label(card, text=icon, font=("Segoe UI Emoji", 28), bg=CARD, fg=color).pack(pady=(20, 4))
        tk.Label(card, text=title, font=("Segoe UI", 14, "bold"), bg=CARD, fg=NAVY).pack()
        tk.Label(card, text=subtitle, font=("Segoe UI", 9), bg=CARD, fg=MUTED,
                 wraplength=280, justify="center").pack(padx=18, pady=(5, 15))
        make_button(card, button_text, command, color, color, width=22, height=1, font_size=10).pack(pady=(0, 20))

    portal_card(
        0, "👤", "Passenger", "Access your wallet, account and travel information.",
        "PASSENGER LOGIN", lambda: show_page("user_login"), "#7C3AED"
    )
    portal_card(
        1, "👨‍✈️", "Driver", "Operate the bus, scan passengers and manage trips.",
        "DRIVER LOGIN", lambda: show_page("driver_login"), BLUE
    )

    # Registration gets its own prominent action — it is NOT hidden inside Driver.
    register_card = tk.Frame(body, bg=LIGHT_BLUE, highlightbackground="#C7DBF7", highlightthickness=1)
    register_card.pack(fill="x", pady=(18, 0))

    left = tk.Frame(register_card, bg=LIGHT_BLUE)
    left.pack(side="left", fill="both", expand=True, padx=20, pady=15)
    tk.Label(left, text="📝  New to SmartBus?", font=("Segoe UI", 12, "bold"),
             bg=LIGHT_BLUE, fg=NAVY).pack(anchor="w")
    tk.Label(left, text="Create a passenger account and register your face for fast boarding.",
             font=("Segoe UI", 9), bg=LIGHT_BLUE, fg=MUTED).pack(anchor="w", pady=(2, 0))

    make_button(
        register_card, "REGISTER AS PASSENGER", open_driver_registration,
        GREEN, GREEN_DARK, width=23, height=1, font_size=10
    ).pack(side="right", padx=20, pady=18)

    tk.Label(
        body, text="🔐 Super Admin access is available from the administration console.",
        font=("Segoe UI", 8), bg=BG, fg=MUTED
    ).pack(pady=(18, 0))

    return frame


# ============================================================
# PAGE: DRIVER LOGIN
# ============================================================

def build_driver_login():
    frame = tk.Frame(container, bg=BG)
    make_portal_nav_bar(frame, "driver_login")

    card = tk.Frame(frame, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    card.place(relx=0.5, rely=0.5, anchor="center", width=380, height=360)

    tk.Label(card, text="🚍 Driver Login", font=("Segoe UI", 18, "bold"), bg=CARD, fg=NAVY).pack(pady=(30, 6))
    tk.Label(card, text="Log in with your driver account.", font=("Segoe UI", 9), bg=CARD, fg=MUTED).pack(pady=(0, 20))

    tk.Label(card, text="Username", font=("Segoe UI", 9, "bold"), bg=CARD, fg=TEXT).pack(anchor="w", padx=40)
    username_entry = tk.Entry(card, font=("Segoe UI", 11))
    username_entry.pack(fill="x", padx=40, pady=(2, 12))

    tk.Label(card, text="Password", font=("Segoe UI", 9, "bold"), bg=CARD, fg=TEXT).pack(anchor="w", padx=40)
    password_entry = tk.Entry(card, font=("Segoe UI", 11), show="•")
    password_entry.pack(fill="x", padx=40, pady=(2, 16))

    error_label = tk.Label(card, text="", font=("Segoe UI", 9), bg=CARD, fg=RED)
    error_label.pack()

    def try_login():
        global current_driver

        username = username_entry.get().strip()
        password = password_entry.get()

        if username not in drivers:
            error_label.config(text="Driver not found.")
            return

        if drivers[username]["password_hash"] != hash_password(password):
            error_label.config(text="Incorrect password.")
            return

        current_driver = username
        error_label.config(text="")
        username_entry.delete(0, tk.END)
        password_entry.delete(0, tk.END)
        refresh_admin_header()
        show_page("admin_dashboard")

    make_button(card, "LOG IN", try_login, BLUE, BLUE_DARK, width=20, height=1, font_size=10).pack(pady=(0, 8))
    make_button(card, "← Back", lambda: show_page("role_picker"), "#E8EEF7", "#DCE6F3", width=20, height=1, font_size=9).configure(fg=NAVY, activeforeground=NAVY)

    return frame



# ============================================================
# PAGE: REGISTRATION
# ============================================================

reg_id_label = None
reg_name_entry = None
reg_type_var = None
reg_login_entry = None
reg_password_entry = None


def register_new_passenger():
    new_id = generate_next_id()
    new_name = reg_name_entry.get().strip()
    new_type = reg_type_var.get()
    login_id = reg_login_entry.get().strip()
    smartbus_password = reg_password_entry.get()

    if not new_name or not login_id or not smartbus_password:
        messagebox.showerror("Missing information", "Please fill in all passenger details.")
        return

    if len(smartbus_password) < 6:
        messagebox.showerror("Weak password", "Passenger password must contain at least 6 characters.")
        return

    # The Login ID must be unique for each passenger.
    for existing_pid, existing_data in passengers.items():
        if existing_data.get("passenger_login_id") == login_id:
            messagebox.showerror(
                "Duplicate Login ID",
                f"This Login ID is already linked to passenger {existing_pid} ({existing_data.get('name', 'Unknown')})."
            )
            return

    if any(str(pid) == str(new_id) for pid in passengers):
        messagebox.showerror("Registration error", "The generated passenger ID already exists. Please try again.")
        return

    discount_map = {"Regular": 0.00, "Student": 0.45, "Senior": 0.50}
    discount = discount_map[new_type]
    os.makedirs("faces", exist_ok=True)

    camera = cv2.VideoCapture(0)

    # ---- Liveness check first: reject registering a photo/video as identity ----
    is_live, reason = liveness.run_liveness_check(camera, face_detector, eye_cascade)

    if not is_live:
        camera.release()
        cv2.destroyAllWindows()
        messagebox.showwarning("Liveness Check Failed", reason)
        return

    if "flagged" in reason.lower():
        messagebox.showinfo("Liveness Notice", reason)

    captured = False
    messagebox.showinfo("Face Capture", "Look at camera, SPACE to capture, Q to cancel.")

    while True:
        success, frame = camera.read()
        if not success:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.imshow("Register New Passenger", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord(" ") and len(faces) == 1:
            x, y, w, h = faces[0]
            cv2.imwrite(f"faces/{new_id}.jpg", gray[y:y+h, x:x+w])
            captured = True
            break
        elif key == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

    if not captured:
        messagebox.showwarning("Cancelled", "No face captured.")
        return

    passengers[new_id] = {
        "name": new_name,
        "type": new_type.lower(),
        "discount": discount,
        "balance": 0,
        "passenger_login_id": login_id,
        "password_hash": hash_password(smartbus_password)
    }
    save_passengers()

    messagebox.showinfo("Registered", f"{new_name} (ID {new_id}) added.\nThey can now log into the Passenger Portal using their Passenger ID and the password just set.")
    reg_id_label.config(text=generate_next_id())

    retrain_recognizer()
    reg_name_entry.delete(0, tk.END)
    reg_login_entry.delete(0, tk.END)
    reg_password_entry.delete(0, tk.END)
    reg_type_var.set("Regular")


def open_driver_registration():
    # Public passenger registration entry point from the SmartBus home screen.
    # The function name is retained for compatibility with existing callbacks.
    reg_id_label.config(text=generate_next_id())
    show_page("registration")


def build_registration():
    global reg_id_label, reg_name_entry, reg_type_var, reg_login_entry, reg_password_entry

    frame = tk.Frame(container, bg=BG)
    make_portal_nav_bar(frame, "registration")

    inner = tk.Frame(frame, bg=BG)
    inner.pack(fill="both", expand=True, padx=40, pady=30)

    tk.Label(inner, text="📝 Create Passenger Account", font=("Segoe UI", 20, "bold"), bg=BG, fg=NAVY).pack(anchor="w")
    tk.Label(inner, text="Register your SmartBus account and face once. Your face can then be used for boarding and exit.", font=("Segoe UI", 10), bg=BG, fg=MUTED).pack(anchor="w", pady=(2, 20))

    card = tk.Frame(inner, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    card.pack(fill="x")

    form = tk.Frame(card, bg=CARD)
    form.pack(fill="x", padx=18, pady=15)

    tk.Label(form, text="Passenger ID (auto-assigned)", font=("Segoe UI", 10, "bold"), bg=CARD, fg=TEXT).grid(row=0, column=0, sticky="w")
    reg_id_label = tk.Label(form, text=generate_next_id(), font=("Segoe UI", 11, "bold"), bg=CARD, fg=BLUE)
    reg_id_label.grid(row=1, column=0, sticky="w", padx=(0, 15), pady=(0, 10))

    tk.Label(form, text="Passenger Name", font=("Segoe UI", 10, "bold"), bg=CARD, fg=TEXT).grid(row=0, column=1, sticky="w")
    reg_name_entry = tk.Entry(form, font=("Segoe UI", 11), width=25)
    reg_name_entry.grid(row=1, column=1, sticky="w", pady=(0, 10))

    tk.Label(form, text="Passenger Type", font=("Segoe UI", 10, "bold"), bg=CARD, fg=TEXT).grid(row=2, column=0, sticky="w")
    reg_type_var = tk.StringVar(value="Regular")
    tk.OptionMenu(form, reg_type_var, "Regular", "Student", "Senior").grid(row=3, column=0, sticky="w", pady=(0, 10))

    tk.Label(form, text="Login ID", font=("Segoe UI", 10, "bold"), bg=CARD, fg=TEXT).grid(row=2, column=1, sticky="w")
    reg_login_entry = tk.Entry(form, font=("Segoe UI", 11), width=25)
    reg_login_entry.grid(row=3, column=1, sticky="w", pady=(0, 10))

    tk.Label(form, text="Create SmartBus Password", font=("Segoe UI", 10, "bold"), bg=CARD, fg=TEXT).grid(row=4, column=0, columnspan=2, sticky="w")
    reg_password_entry = tk.Entry(form, font=("Segoe UI", 11), width=25, show="•")
    reg_password_entry.grid(row=5, column=0, sticky="w", pady=(0, 10))

    make_button(form, "📷  CAPTURE FACE & CREATE ACCOUNT", register_new_passenger, BLUE, BLUE_DARK, width=28, height=2, font_size=10).grid(row=5, column=1, sticky="w", pady=(0, 10))

    back_button = make_button(inner, "← Back", lambda: show_page("role_picker"), "#E8EEF7", "#DCE6F3", width=16, height=1, font_size=9)
    back_button.configure(fg=NAVY, activeforeground=NAVY)
    back_button.pack(anchor="w", pady=(16, 0))

    return frame


# ============================================================
# PAGE: PASSENGER (USER) LOGIN
# ============================================================

def build_user_login():
    frame = tk.Frame(container, bg=BG)
    make_portal_nav_bar(frame, "user_login")

    card = tk.Frame(frame, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    card.place(relx=0.5, rely=0.5, anchor="center", width=380, height=320)

    tk.Label(card, text="👤 Passenger Login", font=("Segoe UI", 18, "bold"), bg=CARD, fg=NAVY).pack(pady=(30, 6))
    tk.Label(card, text="Log in with your Login ID and SmartBus password.", font=("Segoe UI", 9), bg=CARD, fg=MUTED, wraplength=300, justify="center").pack(pady=(0, 20))

    tk.Label(card, text="Login ID", font=("Segoe UI", 9, "bold"), bg=CARD, fg=TEXT).pack(anchor="w", padx=40)
    esewa_entry = tk.Entry(card, font=("Segoe UI", 11))
    esewa_entry.pack(fill="x", padx=40, pady=(2, 12))

    tk.Label(card, text="Password", font=("Segoe UI", 9, "bold"), bg=CARD, fg=TEXT).pack(anchor="w", padx=40)
    password_entry = tk.Entry(card, font=("Segoe UI", 11), show="•")
    password_entry.pack(fill="x", padx=40, pady=(2, 16))

    error_label = tk.Label(card, text="", font=("Segoe UI", 9), bg=CARD, fg=RED)
    error_label.pack()

    def try_login():
        passenger_id_field = esewa_entry.get().strip()
        password = password_entry.get()

        matched_pid = None
        for pid, data in passengers.items():
            if data.get("passenger_login_id") == passenger_id_field:
                matched_pid = pid
                break

        if matched_pid is None:
            error_label.config(text="No account found with that Passenger ID.")
            return

        if passengers[matched_pid].get("password_hash") != hash_password(password):
            error_label.config(text="Incorrect password.")
            return

        error_label.config(text="")
        esewa_entry.delete(0, tk.END)
        password_entry.delete(0, tk.END)
        open_user_dashboard(matched_pid)
        show_page("user_dashboard")

    make_button(card, "LOG IN", try_login, "#7C3AED", "#6D28D9", width=20, height=1, font_size=10).pack(pady=(0, 8))
    make_button(card, "← Back", lambda: show_page("role_picker"), "#E8EEF7", "#DCE6F3", width=20, height=1, font_size=9).configure(fg=NAVY, activeforeground=NAVY)

    return frame


# ============================================================
# PAGE: PASSENGER (USER) DASHBOARD
# ============================================================

current_user_pid = None
user_name_label = None
user_balance_label = None
user_history_label = None
user_photo_label = None


def open_user_dashboard(pid):
    global current_user_pid
    current_user_pid = pid
    refresh_user_dashboard()


def refresh_user_dashboard():
    if current_user_pid is None:
        return

    info = passengers[current_user_pid]
    photo_path = f"faces/{current_user_pid}.jpg"
    if os.path.exists(photo_path):
        photo_image = Image.open(photo_path).convert("RGB")
        photo_image = ImageOps.fit(photo_image, (210, 210), method=Image.Resampling.LANCZOS)
        photo_tk = ImageTk.PhotoImage(photo_image)
        user_photo_label.config(image=photo_tk, text="")
        user_photo_label.image = photo_tk   # keep reference, avoid garbage collection
    else:
        user_photo_label.config(image="", text="No photo on file")

    user_name_label.config(
        text=(
            f"👤 {info['name']}\n"
            f"Passenger ID: {current_user_pid}   •   Type: {info['type']}"
        )
    )
    user_balance_label.config(text=f"Rs. {info.get('balance', 0):.2f}")

    rides = [t for t in transaction_history if str(t["id"]) == str(current_user_pid)]
    if not rides:
        user_history_label.config(text="No rides yet.")
    else:
        text = ""
        for t in rides[-5:]:
            text += f"{t['distance']:.1f} km   •   Rs. {t['fare']:.2f}   •   {t.get('payment_method', 'Wallet')}\n"
        user_history_label.config(text=text.rstrip())


def build_user_dashboard():
    global user_name_label, user_balance_label, user_history_label, user_photo_label

    frame = tk.Frame(container, bg=BG)
    make_portal_nav_bar(frame, "user_login")

    inner = tk.Frame(frame, bg=BG)
    inner.place(relx=0.5, rely=0.5, anchor="center")

    profile_card = tk.Frame(inner, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    profile_card.pack(fill="x", pady=(0, 16))

    profile_inner = tk.Frame(profile_card, bg=CARD)
    profile_inner.pack(fill="x", padx=22, pady=22)

    user_photo_label = tk.Label(
        profile_inner, text="No Photo", font=("Segoe UI", 9, "bold"), bg="#E8EEF7", fg=MUTED,
        width=28, height=14
    )
    user_photo_label.pack(side="left", padx=(0, 18))

    profile_text = tk.Frame(profile_inner, bg=CARD)
    profile_text.pack(side="left", fill="both", expand=True)
    tk.Label(profile_text, text="MY PROFILE", font=("Segoe UI", 9, "bold"), bg=CARD, fg=MUTED).pack(anchor="w")
    user_name_label = tk.Label(profile_text, text="", font=("Segoe UI", 14, "bold"), bg=CARD, fg=NAVY, justify="left", anchor="w")
    user_name_label.pack(anchor="w", pady=(5, 0))

    balance_card = tk.Frame(inner, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    balance_card.pack(fill="x", pady=(0, 16))

    tk.Label(balance_card, text="WALLET BALANCE", font=("Segoe UI", 9, "bold"), bg=CARD, fg=MUTED).pack(anchor="w", padx=20, pady=(15, 0))
    user_balance_label = tk.Label(balance_card, text="Rs. --", font=("Segoe UI", 28, "bold"), bg=CARD, fg=NAVY)
    user_balance_label.pack(anchor="w", padx=20, pady=(0, 15))

    def demo_recharge(amount):
        """Add demo/test credit directly without opening eSewa."""
        try:
            amount = float(amount)
            passengers[current_user_pid]["balance"] = float(passengers[current_user_pid].get("balance", 0)) + amount
            save_passengers()
            refresh_user_dashboard()
            messagebox.showinfo("Demo Balance Added", f"Rs. {amount:.2f} demo credit added to the wallet.")
        except (KeyError, ValueError, TypeError):
            messagebox.showerror("Demo Top Up Error", "Could not add demo balance.")

    def top_up():
        amount_str = tk.simpledialog.askstring("Top Up", "Enter amount to top up (Rs.):", parent=window)
        if not amount_str:
            return
        try:
            amount = float(amount_str)
        except ValueError:
            messagebox.showerror("Invalid amount", "Please enter a valid number.")
            return

        def handle_result(success, info_result, error):
            if success:
                passengers[current_user_pid]["balance"] = passengers[current_user_pid].get("balance", 0) + amount
                save_passengers()
                refresh_user_dashboard()
                messagebox.showinfo("Top Up Successful", f"Rs. {amount:.2f} added to your wallet.")
            else:
                messagebox.showerror("Payment Failed", error or "eSewa payment failed or was cancelled.")

        esewa_payment.start_esewa_payment(
            amount,
            on_complete=lambda success, info_result, error: window.after(0, handle_result, success, info_result, error)
        )

    # DEMO / TEST BALANCE
    tk.Label(balance_card, text="DEMO BALANCE (TEST ONLY)", font=("Segoe UI", 9, "bold"), bg=CARD, fg=MUTED).pack(anchor="w", padx=20, pady=(0, 6))
    demo_frame = tk.Frame(balance_card, bg=CARD)
    demo_frame.pack(fill="x", padx=20, pady=(0, 10))
    for col, amount in enumerate((50, 100, 1000)):
        demo_button = make_button(
            demo_frame, f"+ Rs. {amount}", lambda value=amount: demo_recharge(value),
            "#E8EEF7", "#DCE6F3", width=10, height=1, font_size=10
        )
        demo_button.configure(fg=NAVY, activeforeground=NAVY)
        demo_button.grid(row=0, column=col, sticky="ew", padx=4)
        demo_frame.columnconfigure(col, weight=1)

    tk.Label(balance_card, text="For demonstration/testing only — no payment required.", font=("Segoe UI", 8), bg=CARD, fg=MUTED).pack(anchor="w", padx=20, pady=(0, 10))

    make_button(balance_card, "💳  TOP UP VIA ESEWA", top_up, BLUE, BLUE_DARK, width=24, height=1, font_size=10).pack(padx=20, pady=(0, 15), anchor="w")

    history_card = tk.Frame(inner, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    history_card.pack(fill="x", pady=(0, 16))

    tk.Label(history_card, text="RECENT RIDES", font=("Segoe UI", 9, "bold"), bg=CARD, fg=MUTED).pack(anchor="w", padx=20, pady=(15, 0))
    user_history_label = tk.Label(history_card, text="No rides yet.", font=("Segoe UI", 10), bg=CARD, fg=TEXT, justify="left", anchor="w")
    user_history_label.pack(fill="x", padx=20, pady=(4, 15))

    make_button(inner, "← Log Out", lambda: show_page("role_picker"), "#E8EEF7", "#DCE6F3", width=16, height=1, font_size=9).configure(fg=NAVY, activeforeground=NAVY)

    return frame


import tkinter.simpledialog  # noqa: E402  (needed for top_up dialog above)


# ============================================================
# PAGE: ADMIN (DRIVER) DASHBOARD
# ============================================================

admin_canvas = None
admin_header_revenue_label = None
distance_label = None
passenger_label = None
onboard_list_label = None
fare_label = None
wallet_label = None
history_label = None


def refresh_admin_header():
    if admin_header_revenue_label is None or current_driver is None:
        return
    data = drivers[current_driver]
    admin_header_revenue_label.config(
        text=f"🚌 {data['bus_id']}   •   Driver: {current_driver}   •   My Total Revenue: Rs. {data['revenue']:.2f}"
    )


def finish_exit(passenger_id, passenger_info, distance_travelled, base_fare,
               final_fare, actual_discount, new_wallet_balance, payment_method="Wallet"):

    transaction = {
        "id": str(passenger_id),
        "name": passenger_info["name"],
        "distance": round(distance_travelled, 2),
        "fare": round(final_fare, 2),
        "payment_method": payment_method,
        "driver": current_driver,
        "bus_id": drivers.get(current_driver, {}).get("bus_id", "Unknown") if current_driver else "Unknown",
        "timestamp": datetime.now().isoformat(timespec="seconds")
    }
    transaction_history.append(transaction)
    save_transactions()
    update_history()

    # Reload before incrementing so an admin-created driver or a newer
    # revenue value is not accidentally overwritten by stale memory.
    if current_driver is not None:
        latest_drivers = load_drivers()
        if current_driver in latest_drivers:
            latest_drivers[current_driver]["revenue"] = float(
                latest_drivers[current_driver].get("revenue", 0.0)
            ) + final_fare
            drivers.clear()
            drivers.update(latest_drivers)
            save_drivers()
            refresh_admin_header()

    fare_label.config(
        text=(
            f"✓  PAYMENT SUCCESSFUL\n"
            f"Rs. {final_fare:.2f}\n"
            f"Base Fare: Rs. {base_fare:.2f}   •   "
            f"Actual Discount: Rs. {actual_discount:.2f}"
        ),
        fg=GREEN_DARK
    )

    passenger_label.config(text="✓ Passenger exited successfully", fg=GREEN)
    wallet_label.config(text=f"Rs. {new_wallet_balance:.2f}")

    del onboard_passengers[str(passenger_id)]
    update_onboard_list()


def update_onboard_list():
    if not onboard_passengers:
        onboard_list_label.config(text="No passengers onboard")
        return

    text = ""
    for pid, data in onboard_passengers.items():
        text += (
            f"👤 ID {pid}   •   {data['info']['name']}   •   "
            f"Entry: {data['entry_distance']:.1f} km   •   "
            f"Wallet: Rs. {data['wallet_balance']:.2f}\n"
        )
    onboard_list_label.config(text=text.rstrip())


def update_history():
    if len(transaction_history) == 0:
        history_label.config(text="No transactions yet")
        return

    text = ""
    for transaction in transaction_history[-5:]:
        stamp = transaction.get("timestamp", "")
        try:
            stamp = datetime.fromisoformat(stamp).strftime("%d %b %H:%M")
        except ValueError:
            stamp = ""
        text += (
            f"ID {transaction['id']}   •   {transaction['name']}   •   "
            f"{transaction['distance']:.1f} km   •   Rs. {transaction['fare']:.2f}   •   "
            f"{transaction.get('payment_method', 'Wallet')}   •   {stamp}\n"
        )
    history_label.config(text=text.rstrip())


def board_passenger():
    detected_id = scan_face()

    if detected_id is None:
        passenger_label.config(text="❌ No passenger recognized.", fg=RED)
        return

    if str(detected_id) in onboard_passengers:
        passenger_label.config(text="⚠ A passenger is already onboard.", fg=AMBER)
        return

    if str(detected_id) not in passengers:
        passenger_label.config(text="❌ Passenger is not registered.", fg=RED)
        return

    current_balance = passengers[str(detected_id)].get("balance", 0)

    if current_balance < 0:
        passenger_label.config(
            text=(
                f"🚫 {passengers[str(detected_id)]['name']} has an outstanding debt of "
                f"Rs. {abs(current_balance):.2f}.\nPlease top up before boarding again."
            ),
            fg=RED
        )
        return

    onboard_passengers[str(detected_id)] = {
        "info": passengers[str(detected_id)],
        "entry_distance": distance,
        "wallet_balance": passengers[str(detected_id)].get("balance", 0)
    }

    wallet_label.config(text=f"Rs. {onboard_passengers[str(detected_id)]['wallet_balance']:.2f}")

    passenger_label.config(
        text=(
            f"👤 {onboard_passengers[str(detected_id)]['info']['name']}\n"
            f"ID: {detected_id}   •   Type: {onboard_passengers[str(detected_id)]['info']['type']}\n"
            f"Entry: {onboard_passengers[str(detected_id)]['entry_distance']:.1f} km   •   "
            f"Wallet: Rs. {onboard_passengers[str(detected_id)]['wallet_balance']:.2f}"
        ),
        fg=GREEN
    )

    update_onboard_list()


def exit_passenger():
    detected_id = scan_face()

    if detected_id is None:
        passenger_label.config(text="❌ Face not recognized.", fg=RED)
        return

    if str(detected_id) not in onboard_passengers:
        passenger_label.config(text="⚠ This passenger is not currently onboard.", fg=AMBER)
        return

    passenger_data = onboard_passengers[str(detected_id)]
    passenger_info = passenger_data["info"]
    entry_distance = passenger_data["entry_distance"]
    wallet_balance = passenger_data["wallet_balance"]

    exit_distance = distance
    distance_travelled = exit_distance - entry_distance

    rate_per_km = 5
    base_fare = max(20, distance_travelled * rate_per_km)

    discount = base_fare * passenger_info["discount"]
    calculated_fare = base_fare - discount
    final_fare = max(calculated_fare, 20)
    actual_discount = base_fare - final_fare

    MIN_WALLET_BALANCE = 20
    payment_window = None

    def pay_with_wallet():
        new_wallet_balance = wallet_balance - final_fare

        passenger_info["balance"] = new_wallet_balance
        passengers[str(detected_id)]["balance"] = new_wallet_balance
        onboard_passengers[str(detected_id)]["wallet_balance"] = new_wallet_balance
        save_passengers()

        if payment_window is not None:
            payment_window.destroy()

        finish_exit(detected_id, passenger_info, distance_travelled, base_fare, final_fare, actual_discount, new_wallet_balance, "Wallet")

    def pay_on_credit():
        if payment_window is not None:
            payment_window.destroy()

        new_wallet_balance = wallet_balance - final_fare   # goes negative — recorded as debt

        passenger_info["balance"] = new_wallet_balance
        passengers[str(detected_id)]["balance"] = new_wallet_balance
        onboard_passengers[str(detected_id)]["wallet_balance"] = new_wallet_balance
        save_passengers()

        finish_exit(detected_id, passenger_info, distance_travelled, base_fare, final_fare, actual_discount, new_wallet_balance, "Credit")

    # Fare is paid ONLY from the passenger wallet when exiting.
    # If the wallet cannot cover the fare while keeping the minimum reserve,
    # do not complete the exit. The passenger can top up separately via eSewa
    # from the Passenger Portal before trying again.
    if wallet_balance - final_fare < MIN_WALLET_BALANCE:
        fare_label.config(
            text=(
                f"⚠ Insufficient wallet balance\n"
                f"Fare: Rs. {final_fare:.2f}   •   "
                f"Wallet: Rs. {wallet_balance:.2f}\n\n"
                "Please top up your wallet before exiting."
            ),
            fg=AMBER
        )
        passenger_label.config(
            text=f"⚠ Exit not completed  •  Insufficient wallet balance",
            fg=AMBER
        )
        return

    pay_with_wallet()


def move_half():
    global distance
    distance += 0.5
    distance_label.config(text=f"{distance:.1f} km")


def move_one():
    global distance
    distance += 1.0
    distance_label.config(text=f"{distance:.1f} km")


def recharge_wallet(amount):
    detected_id = scan_face()

    if detected_id is None:
        passenger_label.config(text="❌ Face not recognized.", fg=RED)
        return

    if str(detected_id) not in onboard_passengers:
        passenger_label.config(text="⚠ This passenger is not currently onboard.", fg=AMBER)
        return

    passenger_data = onboard_passengers[str(detected_id)]
    passenger_info = passenger_data["info"]
    wallet_balance = passenger_data["wallet_balance"]

    wallet_balance += amount

    passenger_info["balance"] = wallet_balance
    passengers[str(detected_id)]["balance"] = wallet_balance
    onboard_passengers[str(detected_id)]["wallet_balance"] = wallet_balance
    save_passengers()

    wallet_label.config(text=f"Rs. {wallet_balance:.2f}")

    passenger_label.config(
        text=(
            f"👤 {passenger_info['name']}\n"
            f"ID: {detected_id}   •   Type: {passenger_info['type']}\n"
            f"Entry: {passenger_data['entry_distance']:.1f} km   •   "
            f"Wallet: Rs. {wallet_balance:.2f}"
        ),
        fg=GREEN
    )

    fare_label.config(
        text=f"💳  WALLET RECHARGED\nAdded: Rs. {amount:.2f}   •   New Balance: Rs. {wallet_balance:.2f}",
        fg=BLUE
    )
    update_onboard_list()


def reset_bus():
    global distance
    distance = 0.0

    onboard_passengers.clear()
    update_onboard_list()

    distance_label.config(text="0.0 km")
    passenger_label.config(text="No passenger currently onboard", fg=MUTED)
    wallet_label.config(text="Rs. --")
    fare_label.config(text="💰  FINAL FARE   Rs. --", fg=NAVY)


def driver_logout():
    global current_driver
    current_driver = None
    show_page("role_picker")


def build_admin_dashboard():
    global admin_canvas, admin_header_revenue_label
    global distance_label, passenger_label, onboard_list_label
    global fare_label, wallet_label, history_label

    frame = tk.Frame(container, bg=BG)
    make_portal_nav_bar(frame, "driver_login")

    # ---- top bar with revenue + logout ----
    topbar = tk.Frame(frame, bg=HEADER_BG, height=50)
    topbar.pack(fill="x")
    topbar.pack_propagate(False)

    admin_header_revenue_label = tk.Label(
        topbar, text="", font=("Segoe UI", 10, "bold"), bg=HEADER_BG, fg="#D7F9E3"
    )
    admin_header_revenue_label.pack(side="left", padx=20)

    make_button(topbar, "Log Out", driver_logout, "#334155", "#1E293B", width=10, height=1, font_size=9).pack(side="right", padx=15, pady=8)

    # ---- scrollable dashboard body ----
    canvas = tk.Canvas(frame, bg=BG, highlightthickness=0)
    scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg=BG)
    scrollable_frame.columnconfigure(0, weight=1)

    scrollable_frame.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    def resize_frame(event):
        canvas.itemconfig(canvas_window, width=event.width)

    canvas.bind("<Configure>", resize_frame)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def scroll(event):
        if canvas.winfo_ismapped():
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", scroll)

    admin_canvas = canvas

    content = tk.Frame(scrollable_frame, bg=BG)
    content.pack(fill="x", padx=28, pady=22)
    content.columnconfigure(0, weight=1)

    # ---- welcome ----
    welcome_frame = tk.Frame(content, bg=BG)
    welcome_frame.grid(row=0, column=0, sticky="ew", pady=(0, 18))
    tk.Label(welcome_frame, text="Dashboard", font=("Segoe UI", 20, "bold"), bg=BG, fg=TEXT).pack(anchor="w")
    tk.Label(welcome_frame, text="Manage passenger boarding, travel distance and automated fare payments.", font=("Segoe UI", 10), bg=BG, fg=MUTED).pack(anchor="w", pady=(3, 0))

    # ---- info cards ----
    info_frame = tk.Frame(content, bg=BG)
    info_frame.grid(row=1, column=0, sticky="ew", pady=(0, 18))
    info_frame.columnconfigure(0, weight=1)
    info_frame.columnconfigure(1, weight=1)

    bus_card = tk.Frame(info_frame, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    bus_card.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
    tk.Label(bus_card, text="BUS STATUS", font=("Segoe UI", 10, "bold"), bg=CARD, fg=MUTED).pack(anchor="w", padx=18, pady=(15, 3))
    bus_value_frame = tk.Frame(bus_card, bg=CARD)
    bus_value_frame.pack(fill="x", padx=18, pady=(0, 15))
    distance_label = tk.Label(bus_value_frame, text="0.0 km", font=("Segoe UI", 24, "bold"), bg=CARD, fg=NAVY)
    distance_label.pack(side="left")
    tk.Label(bus_value_frame, text="  DISTANCE", font=("Segoe UI", 9, "bold"), bg=CARD, fg=MUTED).pack(side="left", pady=(10, 0))
    tk.Label(bus_value_frame, text="⚡ 30 km/h", font=("Segoe UI", 9, "bold"), bg=LIGHT_BLUE, fg=BLUE).pack(side="right", pady=(5, 0))

    passenger_card = tk.Frame(info_frame, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    passenger_card.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
    tk.Label(passenger_card, text="PASSENGER STATUS", font=("Segoe UI", 10, "bold"), bg=CARD, fg=MUTED).pack(anchor="w", padx=18, pady=(15, 3))
    passenger_label = tk.Label(passenger_card, text="No passenger currently onboard", font=("Segoe UI", 11), bg=CARD, fg=MUTED, justify="left", anchor="w", wraplength=420)
    passenger_label.pack(fill="x", padx=18, pady=(2, 15))

    # ---- passenger control ----
    make_section_title(content, "👤", "Passenger Control", "Use face recognition to board or exit a passenger.").grid(row=2, column=0, sticky="ew", pady=(0, 9))

    button_frame = tk.Frame(content, bg=BG)
    button_frame.grid(row=3, column=0, sticky="ew", pady=(0, 20))
    button_frame.columnconfigure(0, weight=1)
    button_frame.columnconfigure(1, weight=1)

    board_button = make_button(button_frame, "🟢  BOARD PASSENGER", board_passenger, GREEN, GREEN_DARK, width=22, height=2, font_size=11)
    exit_button = make_button(button_frame, "🔴  EXIT PASSENGER", exit_passenger, RED, RED_DARK, width=22, height=2, font_size=11)
    board_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))
    exit_button.grid(row=0, column=1, sticky="ew", padx=(6, 0))

    # ---- currently onboard ----
    make_section_title(content, "🚏", "Currently Onboard", "Live list of passengers currently on the bus.").grid(row=4, column=0, sticky="ew", pady=(0, 9))
    onboard_card = tk.Frame(content, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    onboard_card.grid(row=5, column=0, sticky="ew", pady=(0, 20))
    onboard_list_label = tk.Label(onboard_card, text="No passengers onboard", font=("Segoe UI", 10), bg=CARD, fg=MUTED, justify="left", anchor="w")
    onboard_list_label.pack(fill="x", padx=20, pady=15)

    # ---- bus movement ----
    make_section_title(content, "📍", "Bus Movement", "Simulate the bus travelling along its route.").grid(row=6, column=0, sticky="ew", pady=(0, 9))
    move_frame = tk.Frame(content, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    move_frame.grid(row=7, column=0, sticky="ew", pady=(0, 20))
    move_frame.columnconfigure(0, weight=1)
    move_frame.columnconfigure(1, weight=1)

    move_half_button = make_button(move_frame, "+ 0.5 KM", move_half, "#E8EEF7", "#DCE6F3", width=18, height=1, font_size=10)
    move_half_button.configure(fg=NAVY, activeforeground=NAVY)
    move_one_button = make_button(move_frame, "+ 1 KM", move_one, BLUE, BLUE_DARK, width=18, height=1, font_size=10)
    move_half_button.grid(row=0, column=0, sticky="ew", padx=(15, 7), pady=15)
    move_one_button.grid(row=0, column=1, sticky="ew", padx=(7, 15), pady=15)

    # ---- current transaction ----
    make_section_title(content, "💰", "Current Transaction", "Latest fare and payment information.").grid(row=8, column=0, sticky="ew", pady=(0, 9))
    fare_frame = tk.Frame(content, bg=LIGHT_BLUE, highlightbackground="#C7DBF7", highlightthickness=1)
    fare_frame.grid(row=9, column=0, sticky="ew", pady=(0, 20))
    tk.Label(fare_frame, text="FARE RESULT", font=("Segoe UI", 9, "bold"), bg=LIGHT_BLUE, fg=BLUE).pack(anchor="w", padx=20, pady=(15, 0))
    fare_label = tk.Label(fare_frame, text="💰  FINAL FARE   Rs. --", font=("Segoe UI", 18, "bold"), bg=LIGHT_BLUE, fg=NAVY, justify="left")
    fare_label.pack(anchor="w", padx=20, pady=(4, 16))

    # ---- wallet ----
    make_section_title(content, "💳", "Passenger Wallet", "Recharge the active passenger wallet before payment.").grid(row=10, column=0, sticky="ew", pady=(0, 9))
    wallet_frame = tk.Frame(content, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    wallet_frame.grid(row=11, column=0, sticky="ew", pady=(0, 20))
    wallet_balance_frame = tk.Frame(wallet_frame, bg=CARD)
    wallet_balance_frame.pack(fill="x", padx=20, pady=(15, 10))
    tk.Label(wallet_balance_frame, text="AVAILABLE BALANCE", font=("Segoe UI", 9, "bold"), bg=CARD, fg=MUTED).pack(anchor="w")
    wallet_label = tk.Label(wallet_balance_frame, text="Rs. --", font=("Segoe UI", 24, "bold"), bg=CARD, fg=NAVY)
    wallet_label.pack(anchor="w", pady=(2, 0))

    recharge_frame = tk.Frame(wallet_frame, bg=CARD)
    recharge_frame.pack(fill="x", padx=15, pady=(0, 15))
    recharge_frame.columnconfigure(0, weight=1)
    recharge_frame.columnconfigure(1, weight=1)
    recharge_frame.columnconfigure(2, weight=1)

    for col, amount in enumerate((50, 100, 500)):
        recharge_button = make_button(recharge_frame, f"+ Rs. {amount}", lambda value=amount: recharge_wallet(value), "#E8EEF7", "#DCE6F3", width=12, height=1, font_size=10)
        recharge_button.configure(fg=NAVY, activeforeground=NAVY)
        recharge_button.grid(row=0, column=col, sticky="ew", padx=5)

    # ---- transaction history ----
    make_section_title(content, "🧾", "Recent Transactions", "The five most recent successful payments are shown here.").grid(row=12, column=0, sticky="ew", pady=(0, 9))
    history_frame = tk.Frame(content, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    history_frame.grid(row=13, column=0, sticky="ew", pady=(0, 20))
    history_label = tk.Label(history_frame, text="No transactions yet", font=("Segoe UI", 10), bg=CARD, fg=MUTED, justify="left", anchor="w")
    history_label.pack(fill="x", padx=20, pady=15)

    # ---- fare structure ----
    make_section_title(content, "📋", "Fare Structure", "Per-kilometre rate used by SmartBus.").grid(row=14, column=0, sticky="ew", pady=(0, 9))
    fare_structure_frame = tk.Frame(content, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    fare_structure_frame.grid(row=15, column=0, sticky="ew", pady=(0, 20))

    fare_rows = [("Rate", "Rs. 5 / km"), ("Minimum Fare", "Rs. 20")]
    for index, (label_text, value_text) in enumerate(fare_rows):
        row = tk.Frame(fare_structure_frame, bg=CARD)
        row.pack(fill="x", padx=20, pady=(10 if index == 0 else 4, 0))
        tk.Label(row, text=label_text, font=("Segoe UI", 10), bg=CARD, fg=TEXT).pack(side="left")
        tk.Label(row, text=value_text, font=("Segoe UI", 10, "bold"), bg=CARD, fg=NAVY).pack(side="right")

    tk.Label(
        fare_structure_frame,
        text="Minimum wallet reserve: Rs. 20   •   Student: 45% OFF   •   Elder Citizen: 50% OFF",
        font=("Segoe UI", 9, "bold"), bg=LIGHT_BLUE, fg=BLUE
    ).pack(fill="x", padx=20, pady=14)

    # ---- reset ----
    reset_frame = tk.Frame(content, bg=BG)
    reset_frame.grid(row=16, column=0, sticky="ew", pady=(0, 18))
    reset_button = make_button(reset_frame, "↻  RESET BUS", reset_bus, "#E8EEF7", "#DCE6F3", width=18, height=1, font_size=10)
    reset_button.configure(fg=NAVY, activeforeground=NAVY)
    reset_button.pack()

    tk.Label(content, text="SmartBus  •  Automated Distance-Based Fare Collection", font=("Segoe UI", 9), bg=BG, fg=MUTED).grid(row=17, column=0, pady=(0, 15))

    return frame


# ============================================================
# BUILD + REGISTER ALL PAGES
# ============================================================

register_page("role_picker", build_role_picker())
register_page("driver_login", build_driver_login())
register_page("registration", build_registration())
register_page("user_login", build_user_login())
register_page("user_dashboard", build_user_dashboard())
register_page("admin_dashboard", build_admin_dashboard())

show_page("role_picker")

window.mainloop()
