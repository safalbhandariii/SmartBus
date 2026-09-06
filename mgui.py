import tkinter as tk
import cv2
import json
from tkinter import messagebox
import os
import numpy as np
import esewa_payment
from PIL import Image, ImageTk
# ============================================================
# SMARTBUS DATA
# ============================================================

distance = 0.0
speed = 30

onboard_passengers = {}

transaction_history = []

# ============================================================
# UI COLORS — "Transit Ticket" palette
# Deep indigo-night + warm marigold accent + jade for money/success,
# on a warm paper background instead of clinical grey-blue.
# ============================================================

BG = "#F7F4EE"            # warm paper background, not clinical grey
CARD = "#FFFFFF"
NAVY = "#12122B"          # deep indigo-night (header, headings)
BLUE = "#E8482C"          # marigold-red accent (primary actions)
BLUE_DARK = "#C93A20"     # marigold-red, pressed state
GREEN = "#1B7A5A"         # deep jade (money / success)
GREEN_DARK = "#145F45"
RED = "#C0392B"           # brick red (errors/exit) — distinct from accent red
RED_DARK = "#9C2E22"
AMBER = "#C99A2E"         # muted gold (warnings / highlights)
TEXT = "#22222E"
MUTED = "#736F63"         # warm grey, matches paper bg undertone
BORDER = "#E7E1D4"        # warm border, not cool grey
LIGHT_BLUE = "#FBEDE8"    # pale marigold wash
LIGHT_GREEN = "#E9F3EE"   # pale jade wash
LIGHT_RED = "#F8EAE7"
LIGHT_AMBER = "#FBF3E0"


# ============================================================
# LOAD PASSENGER DATABASE
# ============================================================

with open("passengers.json", "r") as file:
    passengers = json.load(file)


# ============================================================
# FACE RECOGNITION
# ============================================================

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("trainer.yml")

face_detector = cv2.CascadeClassifier(
    "haarcascade_frontalface_default.xml"
)


# ============================================================
# MAIN WINDOW
# ============================================================

window = tk.Tk()

window.title("SmartBus - Automated Fare Collection")
window.geometry("980x760")
window.minsize(760, 600)
window.configure(bg=BG)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def make_button(parent, text, command, bg, active_bg,
                width=18, height=2, font_size=11):
    button = tk.Button(
        parent,
        text=text,
        command=command,
        font=("Segoe UI", font_size, "bold"),
        width=width,
        height=height,
        bg=bg,
        fg="white",
        activebackground=active_bg,
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        highlightthickness=0
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

    tk.Label(
        top,
        text=icon,
        font=("Segoe UI Emoji", 17),
        bg=BG,
        fg=NAVY
    ).pack(side="left")

    tk.Label(
        top,
        text=title,
        font=("Segoe UI", 14, "bold"),
        bg=BG,
        fg=NAVY
    ).pack(side="left", padx=(8, 0))

    if subtitle:
        tk.Label(
            frame,
            text=subtitle,
            font=("Segoe UI", 9),
            bg=BG,
            fg=MUTED
        ).pack(anchor="w", padx=(32, 0), pady=(1, 0))

    return frame


# ============================================================
# FIXED HEADER
# ============================================================

header = tk.Frame(
    window,
    bg=NAVY,
    height=92
)
header.pack(fill="x")
header.pack_propagate(False)

header_left = tk.Frame(header, bg=NAVY)
header_left.pack(side="left", padx=28, pady=13)

logo_card = tk.Frame(
    header_left,
    bg="white"
)
logo_card.pack(side="left", padx=(0, 12))

logo_image = Image.open("assets/logo.png")
logo_image = logo_image.resize((140, 50))
logo_photo = ImageTk.PhotoImage(logo_image)

logo = tk.Label(
    logo_card,
    image=logo_photo,
    bg="white"
)
logo.image = logo_photo
logo.pack(padx=6, pady=4)

title_box = tk.Frame(header_left, bg=NAVY)
title_box.pack(side="left")

tk.Label(
    title_box,
    text="I-SCAN",
    font=("Segoe UI", 24, "bold"),
    bg=NAVY,
    fg="white"
).pack(anchor="w")

tk.Label(
    title_box,
    text="Automated Fare Collection System",
    font=("Segoe UI", 10),
    bg=NAVY,
    fg="#E8482C"
).pack(anchor="w")


status_pill = tk.Frame(
    header,
    bg="#23233F"
)
status_pill.pack(
    side="right",
    padx=28,
    pady=27
)

tk.Label(
    status_pill,
    text="●",
    font=("Segoe UI", 11, "bold"),
    bg="#23233F",
    fg="#3FC98A"
).pack(side="left", padx=(12, 4), pady=7)

tk.Label(
    status_pill,
    text="SYSTEM ONLINE",
    font=("Segoe UI", 9, "bold"),
    bg="#23233F",
    fg="#D7F9E3"
).pack(side="left", padx=(0, 12), pady=7)


# ============================================================
# SCROLLABLE MAIN AREA
# ============================================================

canvas = tk.Canvas(
    window,
    bg=BG,
    highlightthickness=0
)

scrollbar = tk.Scrollbar(
    window,
    orient="vertical",
    command=canvas.yview
)

scrollable_frame = tk.Frame(
    canvas,
    bg=BG
)

scrollable_frame.columnconfigure(0, weight=1)

scrollable_frame.bind(
    "<Configure>",
    lambda event: canvas.configure(
        scrollregion=canvas.bbox("all")
    )
)

canvas_window = canvas.create_window(
    (0, 0),
    window=scrollable_frame,
    anchor="nw"
)


def resize_frame(event):
    canvas.itemconfig(
        canvas_window,
        width=event.width
    )


canvas.bind("<Configure>", resize_frame)

canvas.configure(
    yscrollcommand=scrollbar.set
)

canvas.pack(
    side="left",
    fill="both",
    expand=True
)

scrollbar.pack(
    side="right",
    fill="y"
)


def scroll(event):
    canvas.yview_scroll(
        int(-1 * (event.delta / 120)),
        "units"
    )


canvas.bind_all("<MouseWheel>", scroll)


# ============================================================
# MAIN CONTENT CONTAINER
# ============================================================

content = tk.Frame(
    scrollable_frame,
    bg=BG
)
content.pack(
    fill="x",
    padx=28,
    pady=22
)
content.columnconfigure(0, weight=1)


# ============================================================
# WELCOME / STATUS
# ============================================================

welcome_frame = tk.Frame(
    content,
    bg=BG
)
welcome_frame.grid(
    row=0,
    column=0,
    sticky="ew",
    pady=(0, 18)
)

tk.Label(
    welcome_frame,
    text="Dashboard",
    font=("Segoe UI", 20, "bold"),
    bg=BG,
    fg=TEXT
).pack(anchor="w")

tk.Label(
    welcome_frame,
    text="Manage passenger boarding, travel distance and automated fare payments.",
    font=("Segoe UI", 10),
    bg=BG,
    fg=MUTED
).pack(anchor="w", pady=(3, 0))


# ============================================================
# INFORMATION CARDS
# ============================================================

info_frame = tk.Frame(
    content,
    bg=BG
)
info_frame.grid(
    row=1,
    column=0,
    sticky="ew",
    pady=(0, 18)
)

info_frame.columnconfigure(0, weight=1)
info_frame.columnconfigure(1, weight=1)


# -----------------------------
# BUS STATUS CARD
# -----------------------------

bus_card = tk.Frame(
    info_frame,
    bg=CARD,
    highlightbackground=BORDER,
    highlightthickness=1
)
bus_card.grid(
    row=0,
    column=0,
    sticky="nsew",
    padx=(0, 7)
)

tk.Frame(bus_card, bg=BLUE, height=4).pack(fill="x", side="top")

tk.Label(
    bus_card,
    text="BUS STATUS",
    font=("Segoe UI", 10, "bold"),
    bg=CARD,
    fg=MUTED
).pack(anchor="w", padx=18, pady=(15, 3))

bus_value_frame = tk.Frame(bus_card, bg=CARD)
bus_value_frame.pack(fill="x", padx=18, pady=(0, 15))

distance_label = tk.Label(
    bus_value_frame,
    text="0.0 km",
    font=("Segoe UI", 24, "bold"),
    bg=CARD,
    fg=NAVY
)
distance_label.pack(side="left")

tk.Label(
    bus_value_frame,
    text="  DISTANCE",
    font=("Segoe UI", 9, "bold"),
    bg=CARD,
    fg=MUTED
).pack(side="left", pady=(10, 0))

speed_badge = tk.Label(
    bus_value_frame,
    text="⚡ 30 km/h",
    font=("Segoe UI", 9, "bold"),
    bg=LIGHT_BLUE,
    fg=BLUE
)
speed_badge.pack(side="right", pady=(5, 0))


# -----------------------------
# PASSENGER STATUS CARD
# -----------------------------

passenger_card = tk.Frame(
    info_frame,
    bg=CARD,
    highlightbackground=BORDER,
    highlightthickness=1
)
passenger_card.grid(
    row=0,
    column=1,
    sticky="nsew",
    padx=(7, 0)
)

tk.Frame(passenger_card, bg=GREEN, height=4).pack(fill="x", side="top")

tk.Label(
    passenger_card,
    text="PASSENGER STATUS",
    font=("Segoe UI", 10, "bold"),
    bg=CARD,
    fg=MUTED
).pack(anchor="w", padx=18, pady=(15, 3))

passenger_label = tk.Label(
    passenger_card,
    text="No passenger currently onboard",
    font=("Segoe UI", 11),
    bg=CARD,
    fg=MUTED,
    justify="left",
    anchor="w",
    wraplength=420
)
passenger_label.pack(
    fill="x",
    padx=18,
    pady=(2, 15)
)


# ============================================================
# PASSENGER CONTROL
# ============================================================

control_title = make_section_title(
    content,
    "👤",
    "Passenger Control",
    "Use face recognition to board or exit a passenger."
)
control_title.grid(
    row=2,
    column=0,
    sticky="ew",
    pady=(0, 9)
)

button_frame = tk.Frame(
    content,
    bg=BG
)
button_frame.grid(
    row=3,
    column=0,
    sticky="ew",
    pady=(0, 20)
)

button_frame.columnconfigure(0, weight=1)
button_frame.columnconfigure(1, weight=1)

board_button = make_button(
    button_frame,
    "🟢  BOARD PASSENGER",
    None,
    GREEN,
    GREEN_DARK,
    width=22,
    height=2,
    font_size=11
)

exit_button = make_button(
    button_frame,
    "🔴  EXIT PASSENGER",
    None,
    RED,
    RED_DARK,
    width=22,
    height=2,
    font_size=11
)

board_button.grid(
    row=0,
    column=0,
    sticky="ew",
    padx=(0, 6)
)

exit_button.grid(
    row=0,
    column=1,
    sticky="ew",
    padx=(6, 0)
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

def generate_next_id():
    if passengers:
        existing_ids = [int(pid) for pid in passengers.keys() if pid.isdigit()]
        if existing_ids:
            return str(max(existing_ids) + 1)
    return "1"

def register_new_passenger():
    new_id = generate_next_id()
    new_name = reg_name_entry.get().strip()
    new_type = reg_type_var.get()

    if not new_id:
        messagebox.showerror("Missing information", "Enter both ID and name.")
        return
    

    discount_map = {"Regular": 0.00, "Student": 0.45, "Senior": 0.50}
    discount = discount_map[new_type]
    os.makedirs("faces", exist_ok=True)

    camera = cv2.VideoCapture(0)
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

    passengers[new_id] = {"name": new_name, "type": new_type.lower(), "discount": discount}
    with open("passengers.json", "w") as file:
        json.dump(passengers, file, indent=4)

    messagebox.showinfo("Registered", f"{new_name} (ID {new_id}) added.")
    reg_id_label.config(text=generate_next_id())

    retrain_recognizer()
    reg_name_entry.delete(0, tk.END)
    reg_type_var.set("Regular")
register_title = make_section_title(content, "🧾", "Register New Passenger", "Add a passenger and enroll their face.")
register_title.grid(row=16, column=0, sticky="ew", pady=(0, 9))

register_card = tk.Frame(content, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
register_card.grid(row=17, column=0, sticky="ew", pady=(0, 20))

tk.Frame(register_card, bg=BLUE, height=4).pack(fill="x", side="top")

reg_form = tk.Frame(register_card, bg=CARD)
reg_form.pack(fill="x", padx=18, pady=15)

tk.Label(reg_form, text="Passenger ID (auto-assigned)", font=("Segoe UI", 10, "bold"), bg=CARD, fg=TEXT).grid(row=0, column=0, sticky="w")
reg_id_label = tk.Label(reg_form, text=generate_next_id(), font=("Segoe UI", 11, "bold"), bg=CARD, fg=BLUE)
reg_id_label.grid(row=1, column=0, sticky="w", padx=(0, 15), pady=(0, 10))

tk.Label(reg_form, text="Passenger Name", font=("Segoe UI", 10, "bold"), bg=CARD, fg=TEXT).grid(row=0, column=1, sticky="w")
reg_name_entry = tk.Entry(reg_form, font=("Segoe UI", 11), width=25)
reg_name_entry.grid(row=1, column=1, sticky="w", pady=(0, 10))

tk.Label(reg_form, text="Passenger Type", font=("Segoe UI", 10, "bold"), bg=CARD, fg=TEXT).grid(row=2, column=0, sticky="w")
reg_type_var = tk.StringVar(value="Regular")
tk.OptionMenu(reg_form, reg_type_var, "Regular", "Student", "Senior").grid(row=3, column=0, sticky="w", pady=(0, 10))

register_button = make_button(reg_form, "📷  CAPTURE FACE & REGISTER", register_new_passenger, BLUE, BLUE_DARK, width=28, height=2, font_size=10)
register_button.grid(row=3, column=1, sticky="w", pady=(0, 10))

# ============================================================
# CURRENTLY ONBOARD PASSENGERS
# ============================================================

onboard_title = make_section_title(
    content,
    "🚏",
    "Currently Onboard",
    "Live list of passengers currently on the bus."
)
onboard_title.grid(row=18, column=0, sticky="ew", pady=(0, 9))

onboard_card = tk.Frame(content, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
onboard_card.grid(row=19, column=0, sticky="ew", pady=(0, 20))

tk.Frame(onboard_card, bg=GREEN, height=4).pack(fill="x", side="top")

onboard_list_label = tk.Label(
    onboard_card,
    text="No passengers onboard",
    font=("Segoe UI", 10),
    bg=CARD,
    fg=MUTED,
    justify="left",
    anchor="w"
)
onboard_list_label.pack(fill="x", padx=20, pady=15)


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



# ============================================================
# FINISH EXIT (shared by wallet + eSewa payment paths)
# ============================================================

def finish_exit(passenger_id, passenger_info, distance_travelled, base_fare, final_fare, actual_discount, new_wallet_balance):

    transaction_history.append({
        "id": passenger_id,
        "name": passenger_info["name"],
        "distance": distance_travelled,
        "fare": final_fare
    })

    update_history()

    fare_label.config(
        text=(
            f"✓  PAYMENT SUCCESSFUL\n"
            f"Rs. {final_fare:.2f}\n"
            f"Base Fare: Rs. {base_fare:.2f}   •   "
            f"Actual Discount: Rs. {actual_discount:.2f}"
        ),
        fg=GREEN_DARK
    )

    passenger_label.config(
        text="✓ Passenger exited successfully",
        fg=GREEN
    )

    wallet_label.config(
        text=f"Rs. {new_wallet_balance:.2f}"
    )

    del onboard_passengers[str(passenger_id)]
    update_onboard_list()

# ============================================================
# FACE SCANNER
# ============================================================

def scan_face():

    camera = cv2.VideoCapture(0)

    detected_id = None

    while True:

        success, frame = camera.read()

        if not success:
            break

        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )

        faces = face_detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(50, 50)
        )

        for (x, y, w, h) in faces:

            face_id, confidence = recognizer.predict(
                gray[y:y+h, x:x+w]
            )

            if confidence < 70:
                detected_id = face_id
                text = f"Passenger {face_id}"
            else:
                text = "Unknown"

            cv2.rectangle(
                frame,
                (x, y),
                (x+w, y+h),
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                text,
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

        cv2.imshow(
            "SmartBus - Face Scanner",
            frame
        )

        key = cv2.waitKey(1) & 0xFF

        if detected_id is not None:
            break

        if key == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

    return detected_id


# ============================================================
# BOARD PASSENGER
# ============================================================

def board_passenger():

    detected_id = scan_face()                          # 1. scan FIRST

    if detected_id is None:                             # 2. check None
        passenger_label.config(text="❌ No passenger recognized.", fg=RED)
        return

    if str(detected_id) in onboard_passengers:           # 3. check already onboard
        passenger_label.config(text="⚠ A passenger is already onboard.", fg=AMBER)
        return

    if str(detected_id) not in passengers:               # 4. check registered
        passenger_label.config(text="❌ Passenger is not registered.", fg=RED)
        return

    onboard_passengers[str(detected_id)] = {             # 5. dict write LAST
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

# ============================================================
# EXIT PASSENGER
# ============================================================

def exit_passenger():

    detected_id = scan_face()

    if detected_id is None:
        passenger_label.config(
            text="❌ Face not recognized.",
            fg=RED
        )
        return

    if str(detected_id) not in onboard_passengers:
        passenger_label.config(
            text="⚠ This passenger is not currently onboard.",
            fg=AMBER
        )
        return

    passenger_data = onboard_passengers[str(detected_id)]
    passenger_info = passenger_data["info"]
    entry_distance = passenger_data["entry_distance"]
    wallet_balance = passenger_data["wallet_balance"]

    exit_distance = distance
    distance_travelled = exit_distance - entry_distance

    # -----------------------------
    # KATHMANDU VALLEY FARE
    # -----------------------------

    rate_per_km = 5
    base_fare = max(20, distance_travelled * rate_per_km)

    # -----------------------------
    # DISCOUNT
    # -----------------------------

    discount = base_fare * passenger_info["discount"]
    calculated_fare = base_fare - discount
    final_fare = max(calculated_fare, 20)
    actual_discount = base_fare - final_fare

    # -----------------------------
    # PAYMENT OPTIONS
    # -----------------------------

    MIN_WALLET_BALANCE = 20

    def pay_with_wallet():
        new_wallet_balance = wallet_balance - final_fare

        passenger_info["balance"] = new_wallet_balance
        passengers[str(detected_id)]["balance"] = new_wallet_balance
        onboard_passengers[str(detected_id)]["wallet_balance"] = new_wallet_balance

        with open("passengers.json", "w") as file:
            json.dump(passengers, file, indent=4)

        payment_window.destroy()

        finish_exit(
            detected_id,
            passenger_info,
            distance_travelled,
            base_fare,
            final_fare,
            actual_discount,
            new_wallet_balance
        )

    def pay_with_esewa():
        payment_window.destroy()

        fare_label.config(
            text=f"Opening eSewa to pay Rs. {final_fare:.2f}...",
            fg=AMBER
        )

        def handle_esewa_result(success, info, error):
            if success:
                finish_exit(
                    detected_id,
                    passenger_info,
                    distance_travelled,
                    base_fare,
                    final_fare,
                    actual_discount,
                    wallet_balance
                )
            else:
                fare_label.config(
                    text=f"🔴 eSewa payment failed or cancelled.\n{error or ''}",
                    fg=RED
                )
                passenger_label.config(
                    text=f"⚠ Payment failed  •  Passenger: {passenger_info['name']}",
                    fg=RED
                )

        esewa_payment.start_esewa_payment(
            final_fare,
            on_complete=lambda success, info, error:
                window.after(0, handle_esewa_result, success, info, error)
        )

    # If wallet cannot pay while maintaining the Rs. 20 minimum,
    # eSewa opens automatically.
    if wallet_balance - final_fare < MIN_WALLET_BALANCE:
        pay_with_esewa()
        return

    # If wallet is sufficient, let the passenger choose.
    payment_window = tk.Toplevel(window)
    payment_window.title("Choose Payment Method")
    payment_window.geometry("380x240")
    payment_window.resizable(False, False)
    payment_window.configure(bg=CARD)
    payment_window.transient(window)
    payment_window.grab_set()

    tk.Frame(payment_window, bg=BLUE, height=4).pack(fill="x", side="top")

    tk.Label(
        payment_window,
        text="Choose Payment Method",
        font=("Segoe UI", 16, "bold"),
        bg=CARD,
        fg=NAVY
    ).pack(pady=(22, 6))

    tk.Label(
        payment_window,
        text=(
            f"Fare: Rs. {final_fare:.2f}\n"
            f"Wallet Balance: Rs. {wallet_balance:.2f}"
        ),
        font=("Segoe UI", 10),
        bg=CARD,
        fg=MUTED,
        justify="center"
    ).pack(pady=(0, 16))

    option_frame = tk.Frame(payment_window, bg=CARD)
    option_frame.pack(fill="x", padx=25)

    wallet_button = make_button(
        option_frame,
        "💳  PAY WITH WALLET",
        pay_with_wallet,
        GREEN,
        GREEN_DARK,
        width=17,
        height=2,
        font_size=10
    )
    wallet_button.pack(side="left", padx=(0, 6), expand=True, fill="x")

    esewa_button = make_button(
        option_frame,
        "🟢  PAY WITH ESEWA",
        pay_with_esewa,
        BLUE,
        BLUE_DARK,
        width=17,
        height=2,
        font_size=10
    )
    esewa_button.pack(side="right", padx=(6, 0), expand=True, fill="x")

# ============================================================
# CONNECT BUTTONS
# ============================================================

board_button.configure(command=board_passenger)
exit_button.configure(command=exit_passenger)


# ============================================================
# BUS MOVEMENT
# ============================================================

movement_title = make_section_title(
    content,
    "📍",
    "Bus Movement",
    "Simulate the bus travelling along its route."
)
movement_title.grid(
    row=4,
    column=0,
    sticky="ew",
    pady=(0, 9)
)

move_frame = tk.Frame(
    content,
    bg=CARD,
    highlightbackground=BORDER,
    highlightthickness=1
)
move_frame.grid(
    row=5,
    column=0,
    sticky="ew",
    pady=(0, 20)
)

move_frame.columnconfigure(0, weight=1)
move_frame.columnconfigure(1, weight=1)

def move_half():

    global distance

    distance += 0.5

    distance_label.config(
        text=f"{distance:.1f} km"
    )


def move_one():

    global distance

    distance += 1.0

    distance_label.config(
        text=f"{distance:.1f} km"
    )


move_half_button = make_button(
    move_frame,
    "+ 0.5 KM",
    move_half,
    "#EFEAD9",
    "#E4DCC4",
    width=18,
    height=1,
    font_size=10
)
move_half_button.configure(
    fg=NAVY,
    activeforeground=NAVY
)

move_one_button = make_button(
    move_frame,
    "+ 1 KM",
    move_one,
    BLUE,
    BLUE_DARK,
    width=18,
    height=1,
    font_size=10
)

move_half_button.grid(
    row=0,
    column=0,
    sticky="ew",
    padx=(15, 7),
    pady=15
)

move_one_button.grid(
    row=0,
    column=1,
    sticky="ew",
    padx=(7, 15),
    pady=15
)


# ============================================================
# CURRENT TRANSACTION
# ============================================================

transaction_title = make_section_title(
    content,
    "💰",
    "Current Transaction",
    "Latest fare and payment information."
)
transaction_title.grid(
    row=6,
    column=0,
    sticky="ew",
    pady=(0, 9)
)

fare_frame = tk.Frame(
    content,
    bg=LIGHT_BLUE,
    highlightbackground="#C7DBF7",
    highlightthickness=1
)
fare_frame.grid(
    row=7,
    column=0,
    sticky="ew",
    pady=(0, 20)
)

tk.Label(
    fare_frame,
    text="FARE RESULT",
    font=("Segoe UI", 9, "bold"),
    bg=LIGHT_BLUE,
    fg=BLUE
).pack(
    anchor="w",
    padx=20,
    pady=(15, 0)
)

fare_label = tk.Label(
    fare_frame,
    text="💰  FINAL FARE   Rs. --",
    font=("Segoe UI", 18, "bold"),
    bg=LIGHT_BLUE,
    fg=NAVY,
    justify="left"
)
fare_label.pack(
    anchor="w",
    padx=20,
    pady=(4, 16)
)


# ============================================================
# WALLET
# ============================================================

wallet_title = make_section_title(
    content,
    "💳",
    "Passenger Wallet",
    "Recharge the active passenger wallet before payment."
)
wallet_title.grid(
    row=8,
    column=0,
    sticky="ew",
    pady=(0, 9)
)

wallet_frame = tk.Frame(
    content,
    bg=CARD,
    highlightbackground=BORDER,
    highlightthickness=1
)
wallet_frame.grid(
    row=9,
    column=0,
    sticky="ew",
    pady=(0, 20)
)

tk.Frame(wallet_frame, bg=AMBER, height=4).pack(fill="x", side="top")

wallet_balance_frame = tk.Frame(
    wallet_frame,
    bg=CARD
)
wallet_balance_frame.pack(
    fill="x",
    padx=20,
    pady=(15, 10)
)

tk.Label(
    wallet_balance_frame,
    text="AVAILABLE BALANCE",
    font=("Segoe UI", 9, "bold"),
    bg=CARD,
    fg=MUTED
).pack(anchor="w")

wallet_label = tk.Label(
    wallet_balance_frame,
    text="Rs. --",
    font=("Segoe UI", 24, "bold"),
    bg=CARD,
    fg=NAVY
)
wallet_label.pack(anchor="w", pady=(2, 0))


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

    with open("passengers.json", "w") as file:
        json.dump(passengers, file, indent=4)

    wallet_label.config(
        text=f"Rs. {wallet_balance:.2f}"
    )

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
        text=(
            f"💳  WALLET RECHARGED\n"
            f"Added: Rs. {amount:.2f}   •   "
            f"New Balance: Rs. {wallet_balance:.2f}"
        ),
        fg=BLUE
    )
    update_onboard_list()


recharge_frame = tk.Frame(
    wallet_frame,
    bg=CARD
)
recharge_frame.pack(
    fill="x",
    padx=15,
    pady=(0, 15)
)

recharge_frame.columnconfigure(0, weight=1)
recharge_frame.columnconfigure(1, weight=1)
recharge_frame.columnconfigure(2, weight=1)

for col, amount in enumerate((50, 100, 500)):

    recharge_button = make_button(
        recharge_frame,
        f"+ Rs. {amount}",
        lambda value=amount: recharge_wallet(value),
        "#EFEAD9",
        "#E4DCC4",
        width=12,
        height=1,
        font_size=10
    )

    recharge_button.configure(
        fg=NAVY,
        activeforeground=NAVY
    )

    recharge_button.grid(
        row=0,
        column=col,
        sticky="ew",
        padx=5
    )


# ============================================================
# TRANSACTION HISTORY
# ============================================================

history_title = make_section_title(
    content,
    "🧾",
    "Recent Transactions",
    "The five most recent successful payments are shown here."
)
history_title.grid(
    row=10,
    column=0,
    sticky="ew",
    pady=(0, 9)
)

history_frame = tk.Frame(
    content,
    bg=CARD,
    highlightbackground=BORDER,
    highlightthickness=1
)
history_frame.grid(
    row=11,
    column=0,
    sticky="ew",
    pady=(0, 20)
)

tk.Frame(history_frame, bg=NAVY, height=4).pack(fill="x", side="top")

history_label = tk.Label(
    history_frame,
    text="No transactions yet",
    font=("Segoe UI", 10),
    bg=CARD,
    fg=MUTED,
    justify="left",
    anchor="w"
)
history_label.pack(
    fill="x",
    padx=20,
    pady=15
)


def update_history():

    if len(transaction_history) == 0:

        history_label.config(
            text="No transactions yet"
        )

        return

    text = ""

    for transaction in transaction_history[-5:]:

        text += (
            f"ID {transaction['id']}   •   "
            f"{transaction['name']}   •   "
            f"{transaction['distance']:.1f} km   •   "
            f"Rs. {transaction['fare']:.2f}   ✓ Paid\n"
        )

    history_label.config(
        text=text.rstrip()
    )


# ============================================================
# FARE STRUCTURE
# ============================================================

fare_title = make_section_title(
    content,
    "📋",
    "Fare Structure",
    "Kathmandu Valley fare bands used by SmartBus."
)
fare_title.grid(
    row=12,
    column=0,
    sticky="ew",
    pady=(0, 9)
)

fare_structure_frame = tk.Frame(
    content,
    bg=CARD,
    highlightbackground=BORDER,
    highlightthickness=1
)
fare_structure_frame.grid(
    row=13,
    column=0,
    sticky="ew",
    pady=(0, 20)
)

tk.Frame(fare_structure_frame, bg=AMBER, height=4).pack(fill="x", side="top")

fare_rows = [
    ("0 – 5 KM", "Rs. 24"),
    ("5 – 10 KM", "Rs. 33"),
    ("10 – 15 KM", "Rs. 39"),
    ("15 – 20 KM", "Rs. 44"),
    ("20+ KM", "Rs. 50"),
]

for index, (distance_range, fare) in enumerate(fare_rows):

    row = tk.Frame(
        fare_structure_frame,
        bg=CARD
    )
    row.pack(
        fill="x",
        padx=20,
        pady=(10 if index == 0 else 4, 0)
    )

    tk.Label(
        row,
        text=distance_range,
        font=("Segoe UI", 10),
        bg=CARD,
        fg=TEXT
    ).pack(side="left")

    tk.Label(
        row,
        text=fare,
        font=("Segoe UI", 10, "bold"),
        bg=CARD,
        fg=NAVY
    ).pack(side="right")

tk.Label(
    fare_structure_frame,
    text="Minimum payable fare: Rs. 20   •   Student: 45% OFF   •   Elder Citizen: 50% OFF",
    font=("Segoe UI", 9, "bold"),
    bg=LIGHT_BLUE,
    fg=BLUE
).pack(
    fill="x",
    padx=20,
    pady=14
)


# ============================================================
# RESET BUS
# ============================================================

def reset_bus():

    global distance
    # global passenger_id
    # global entry_distance
    # global passenger_info
    global wallet_balance

    # distance = 0.0
    # passenger_id = None
    # entry_distance = None
    # passenger_info = None
    # wallet_balance = 0

    onboard_passengers.clear()
    update_onboard_list()

    distance_label.config(
        text="0.0 km"
    )

    passenger_label.config(
        text="No passenger currently onboard",
        fg=MUTED
    )

    wallet_label.config(
        text="Rs. --"
    )

    fare_label.config(
        text="💰  FINAL FARE   Rs. --",
        fg=NAVY
    )


reset_frame = tk.Frame(
    content,
    bg=BG
)
reset_frame.grid(
    row=14,
    column=0,
    sticky="ew",
    pady=(0, 18)
)

reset_button = make_button(
    reset_frame,
    "↻  RESET BUS",
    reset_bus,
    "#EFEAD9",
    "#E4DCC4",
    width=18,
    height=1,
    font_size=10
)
reset_button.configure(
    fg=NAVY,
    activeforeground=NAVY
)
reset_button.pack()


# ============================================================
# FOOTER
# ============================================================

tk.Label(
    content,
    text="SmartBus  •  Automated Distance-Based Fare Collection",
    font=("Segoe UI", 9),
    bg=BG,
    fg=MUTED
).grid(
    row=15,
    column=0,
    pady=(0, 15)
)


# ============================================================
# START
# ============================================================

window.mainloop()