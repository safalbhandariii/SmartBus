
import tkinter as tk
import cv2
import json
from datetime import datetime

# ============================================================
# SMARTBUS SETTINGS
# ============================================================

MAX_PASSENGERS = 5

distance = 0.0
speed = 30

# passenger_id -> {"info": ..., "entry_distance": ...}
onboard_passengers = {}

transaction_history = []
total_revenue = 0.0
successful_payments = 0
failed_payments = 0

BG = "#F4F7FB"
CARD = "#FFFFFF"
NAVY = "#0F2747"
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
# LOAD PASSENGERS
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
window.geometry("1000x780")
window.minsize(800, 620)
window.configure(bg=BG)

# ============================================================
# HELPERS
# ============================================================

def make_button(parent, text, command, bg, active_bg,
                width=18, height=2, font_size=10):
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

    def enter(event):
        button.configure(bg=active_bg)

    def leave(event):
        button.configure(bg=bg)

    button.bind("<Enter>", enter)
    button.bind("<Leave>", leave)
    return button


def section_title(parent, icon, title, subtitle):
    frame = tk.Frame(parent, bg=BG)
    top = tk.Frame(frame, bg=BG)
    top.pack(fill="x")

    tk.Label(
        top, text=icon, font=("Segoe UI Emoji", 16),
        bg=BG, fg=NAVY
    ).pack(side="left")

    tk.Label(
        top, text=title, font=("Segoe UI", 14, "bold"),
        bg=BG, fg=NAVY
    ).pack(side="left", padx=8)

    tk.Label(
        frame, text=subtitle, font=("Segoe UI", 9),
        bg=BG, fg=MUTED
    ).pack(anchor="w", padx=(31, 0))

    return frame


# ============================================================
# HEADER
# ============================================================

header = tk.Frame(window, bg=NAVY, height=92)
header.pack(fill="x")
header.pack_propagate(False)

left_header = tk.Frame(header, bg=NAVY)
left_header.pack(side="left", padx=28, pady=12)

tk.Label(
    left_header, text="🚌", font=("Segoe UI Emoji", 30),
    bg=NAVY, fg="white"
).pack(side="left", padx=(0, 12))

heading = tk.Frame(left_header, bg=NAVY)
heading.pack(side="left")

tk.Label(
    heading, text="SMARTBUS",
    font=("Segoe UI", 24, "bold"),
    bg=NAVY, fg="white"
).pack(anchor="w")

tk.Label(
    heading, text="Automated Fare Collection System",
    font=("Segoe UI", 10),
    bg=NAVY, fg="#BFD4EA"
).pack(anchor="w")

status = tk.Frame(header, bg="#123B5F")
status.pack(side="right", padx=28, pady=27)

tk.Label(
    status, text="●", font=("Segoe UI", 11, "bold"),
    bg="#123B5F", fg="#4ADE80"
).pack(side="left", padx=(12, 4), pady=7)

tk.Label(
    status, text="SYSTEM ONLINE",
    font=("Segoe UI", 9, "bold"),
    bg="#123B5F", fg="#D7F9E3"
).pack(side="left", padx=(0, 12), pady=7)

# ============================================================
# SCROLL AREA
# ============================================================

canvas = tk.Canvas(window, bg=BG, highlightthickness=0)
scrollbar = tk.Scrollbar(
    window, orient="vertical", command=canvas.yview
)

scrollable = tk.Frame(canvas, bg=BG)
scrollable.columnconfigure(0, weight=1)

scrollable.bind(
    "<Configure>",
    lambda event: canvas.configure(
        scrollregion=canvas.bbox("all")
    )
)

canvas_window = canvas.create_window(
    (0, 0), window=scrollable, anchor="nw"
)

def resize_scrollable(event):
    canvas.itemconfigure(canvas_window, width=event.width)

canvas.bind("<Configure>", resize_scrollable)
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

def mouse_scroll(event):
    canvas.yview_scroll(int(-event.delta / 120), "units")

canvas.bind_all("<MouseWheel>", mouse_scroll)

content = tk.Frame(scrollable, bg=BG)
content.pack(fill="x", padx=28, pady=22)
content.columnconfigure(0, weight=1)

# ============================================================
# DASHBOARD
# ============================================================

tk.Label(
    content, text="Driver Dashboard",
    font=("Segoe UI", 20, "bold"),
    bg=BG, fg=TEXT
).grid(row=0, column=0, sticky="w")

tk.Label(
    content,
    text="Manage up to five passengers simultaneously with face-verified boarding and exit.",
    font=("Segoe UI", 10),
    bg=BG, fg=MUTED
).grid(row=1, column=0, sticky="w", pady=(2, 18))

# ============================================================
# STATUS CARDS
# ============================================================

cards = tk.Frame(content, bg=BG)
cards.grid(row=2, column=0, sticky="ew", pady=(0, 20))
cards.columnconfigure(0, weight=1)
cards.columnconfigure(1, weight=1)

bus_card = tk.Frame(
    cards, bg=CARD, highlightbackground=BORDER, highlightthickness=1
)
bus_card.grid(row=0, column=0, sticky="nsew", padx=(0, 7))

tk.Label(
    bus_card, text="BUS STATUS",
    font=("Segoe UI", 10, "bold"),
    bg=CARD, fg=MUTED
).pack(anchor="w", padx=18, pady=(15, 3))

bus_values = tk.Frame(bus_card, bg=CARD)
bus_values.pack(fill="x", padx=18, pady=(0, 15))

distance_label = tk.Label(
    bus_values, text="0.0 km",
    font=("Segoe UI", 24, "bold"),
    bg=CARD, fg=NAVY
)
distance_label.pack(side="left")

tk.Label(
    bus_values, text="  DISTANCE",
    font=("Segoe UI", 9, "bold"),
    bg=CARD, fg=MUTED
).pack(side="left", pady=(10, 0))

speed_badge = tk.Label(
    bus_values, text="⚡ 30 km/h",
    font=("Segoe UI", 9, "bold"),
    bg=LIGHT_BLUE, fg=BLUE
)
speed_badge.pack(side="right", pady=5)

passenger_card = tk.Frame(
    cards, bg=CARD, highlightbackground=BORDER, highlightthickness=1
)
passenger_card.grid(row=0, column=1, sticky="nsew", padx=(7, 0))

tk.Label(
    passenger_card, text="ONBOARD PASSENGERS",
    font=("Segoe UI", 10, "bold"),
    bg=CARD, fg=MUTED
).pack(anchor="w", padx=18, pady=(15, 3))

count_label = tk.Label(
    passenger_card, text="0 / 5 passengers",
    font=("Segoe UI", 16, "bold"),
    bg=CARD, fg=NAVY
)
count_label.pack(anchor="w", padx=18)

passenger_status_label = tk.Label(
    passenger_card,
    text="No passenger currently onboard",
    font=("Segoe UI", 9),
    bg=CARD, fg=MUTED,
    justify="left", anchor="w"
)
passenger_status_label.pack(
    fill="x", padx=18, pady=(2, 14)
)

# ============================================================
# FACE SCANNER
# ============================================================

def scan_face(title="SmartBus - Face Scanner"):
    camera = cv2.VideoCapture(0)
    detected_id = None

    while True:
        success, frame = camera.read()

        if not success:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

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
                frame, (x, y), (x+w, y+h),
                (0, 255, 0), 2
            )

            cv2.putText(
                frame, text, (x, y-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                (0, 255, 0), 2
            )

        cv2.imshow(title, frame)
        key = cv2.waitKey(1) & 0xFF

        if detected_id is not None:
            break

        if key == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()
    return detected_id

# ============================================================
# UPDATE PASSENGER DISPLAY
# ============================================================

def update_passenger_display():
    count = len(onboard_passengers)

    count_label.config(
        text=f"{count} / {MAX_PASSENGERS} passengers",
        fg=GREEN if count else NAVY
    )

    if count == 0:
        passenger_status_label.config(
            text="No passenger currently onboard",
            fg=MUTED
        )
        onboard_list.delete(0, tk.END)
        selected_wallet_label.config(text="Select a passenger")
        return

    lines = []
    onboard_list.delete(0, tk.END)

    for pid, data in onboard_passengers.items():
        info = data["info"]
        entry = data["entry_distance"]

        lines.append(
            f"👤 {info['name']}  |  ID {pid}  |  Entry {entry:.1f} km"
        )

        onboard_list.insert(
            tk.END,
            f"{info['name']}  |  ID {pid}  |  Rs. {info.get('balance', 0):.2f}"
        )

    passenger_status_label.config(
        text="\n".join(lines),
        fg=TEXT
    )

    if onboard_list.size() > 0 and not onboard_list.curselection():
        onboard_list.selection_set(0)
        update_selected_wallet()

# ============================================================
# BOARD
# ============================================================

def board_passenger():
    if len(onboard_passengers) >= MAX_PASSENGERS:
        fare_label.config(
            text="⚠ BUS CAPACITY REACHED\nMaximum 5 passengers onboard.",
            fg=AMBER
        )
        return

    detected_id = scan_face("SmartBus - Board Passenger")

    if detected_id is None:
        fare_label.config(
            text="❌ No passenger recognized.",
            fg=RED
        )
        return

    pid = str(detected_id)

    if pid not in passengers:
        fare_label.config(
            text="❌ Passenger is not registered.",
            fg=RED
        )
        return

    if detected_id in onboard_passengers:
        fare_label.config(
            text="⚠ Passenger is already onboard.",
            fg=AMBER
        )
        return

    info = passengers[pid]

    onboard_passengers[detected_id] = {
        "info": info,
        "entry_distance": distance
    }

    fare_label.config(
        text=(
            f"✓ PASSENGER BOARDED\n"
            f"{info['name']}  •  ID {detected_id}\n"
            f"Entry Distance: {distance:.1f} km"
        ),
        fg=GREEN_DARK
    )

    update_passenger_display()

# ============================================================
# EXIT
# ============================================================

def exit_passenger():
    global total_revenue
    global successful_payments
    global failed_payments

    if not onboard_passengers:
        fare_label.config(
            text="⚠ No passengers are currently onboard.",
            fg=AMBER
        )
        return

    detected_id = scan_face("SmartBus - Exit Passenger")

    if detected_id is None:
        fare_label.config(
            text="❌ Passenger could not be recognized.",
            fg=RED
        )
        return

    if detected_id not in onboard_passengers:
        fare_label.config(
            text="❌ This passenger is not currently onboard.",
            fg=RED
        )
        return

    passenger_data = onboard_passengers[detected_id]
    info = passenger_data["info"]
    entry_distance = passenger_data["entry_distance"]

    exit_distance = distance
    distance_travelled = max(0, exit_distance - entry_distance)

    # Kathmandu Valley fare
    if distance_travelled <= 5:
        base_fare = 24
    elif distance_travelled <= 10:
        base_fare = 33
    elif distance_travelled <= 15:
        base_fare = 39
    elif distance_travelled <= 20:
        base_fare = 44
    else:
        base_fare = 50

    discount = base_fare * info.get("discount", 0)
    calculated_fare = base_fare - discount
    final_fare = max(calculated_fare, 20)
    actual_discount = base_fare - final_fare

    wallet_balance = info.get("balance", 0)

    if wallet_balance < final_fare:
        failed_payments += 1

        fare_label.config(
            text=(
                f"🔴 DRIVER ALERT — INSUFFICIENT BALANCE\n"
                f"Passenger: {info['name']}  |  ID: {detected_id}\n"
                f"Fare Required: Rs. {final_fare:.2f}   •   "
                f"Wallet: Rs. {wallet_balance:.2f}"
            ),
            fg=RED
        )
        return

    wallet_balance -= final_fare
    info["balance"] = wallet_balance
    passengers[str(detected_id)]["balance"] = wallet_balance

    with open("passengers.json", "w") as file:
        json.dump(passengers, file, indent=4)

    total_revenue += final_fare
    successful_payments += 1

    transaction_history.append({
        "time": datetime.now().strftime("%H:%M"),
        "id": detected_id,
        "name": info["name"],
        "distance": distance_travelled,
        "fare": final_fare
    })

    fare_label.config(
        text=(
            f"✓ PAYMENT SUCCESSFUL\n"
            f"{info['name']}  •  {distance_travelled:.1f} km\n"
            f"Base: Rs. {base_fare:.2f}  •  "
            f"Discount: Rs. {actual_discount:.2f}  •  "
            f"Paid: Rs. {final_fare:.2f}\n"
            f"Remaining Wallet: Rs. {wallet_balance:.2f}"
        ),
        fg=GREEN_DARK
    )

    del onboard_passengers[detected_id]
    update_passenger_display()
    update_history()
    update_summary()

# ============================================================
# MOVEMENT
# ============================================================

def move_half():
    global distance
    distance += 0.5
    distance_label.config(text=f"{distance:.1f} km")

def move_one():
    global distance
    distance += 1.0
    distance_label.config(text=f"{distance:.1f} km")

# ============================================================
# PASSENGER CONTROL
# ============================================================

control_title = section_title(
    content, "👤", "Passenger Control",
    "Board or exit individual passengers using face recognition."
)
control_title.grid(row=3, column=0, sticky="ew", pady=(0, 9))

control_frame = tk.Frame(content, bg=BG)
control_frame.grid(row=4, column=0, sticky="ew", pady=(0, 20))
control_frame.columnconfigure(0, weight=1)
control_frame.columnconfigure(1, weight=1)

board_button = make_button(
    control_frame, "🟢  BOARD PASSENGER",
    board_passenger, GREEN, GREEN_DARK, 22, 2, 11
)
board_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))

exit_button = make_button(
    control_frame, "🔴  EXIT PASSENGER",
    exit_passenger, RED, RED_DARK, 22, 2, 11
)
exit_button.grid(row=0, column=1, sticky="ew", padx=(6, 0))

# ============================================================
# BUS MOVEMENT
# ============================================================

movement_title = section_title(
    content, "📍", "Bus Movement",
    "Simulate route distance for the fare calculation."
)
movement_title.grid(row=5, column=0, sticky="ew", pady=(0, 9))

move_frame = tk.Frame(
    content, bg=CARD,
    highlightbackground=BORDER, highlightthickness=1
)
move_frame.grid(row=6, column=0, sticky="ew", pady=(0, 20))
move_frame.columnconfigure(0, weight=1)
move_frame.columnconfigure(1, weight=1)

half_button = make_button(
    move_frame, "+ 0.5 KM", move_half,
    "#E8EEF7", "#DCE6F3", 18, 1, 10
)
half_button.configure(fg=NAVY, activeforeground=NAVY)
half_button.grid(row=0, column=0, sticky="ew", padx=(15, 7), pady=15)

one_button = make_button(
    move_frame, "+ 1 KM", move_one,
    BLUE, BLUE_DARK, 18, 1, 10
)
one_button.grid(row=0, column=1, sticky="ew", padx=(7, 15), pady=15)

# ============================================================
# CURRENT TRANSACTION
# ============================================================

transaction_title = section_title(
    content, "💰", "Current Transaction",
    "Latest fare, discount and wallet payment information."
)
transaction_title.grid(row=7, column=0, sticky="ew", pady=(0, 9))

fare_frame = tk.Frame(
    content, bg=LIGHT_BLUE,
    highlightbackground="#C7DBF7", highlightthickness=1
)
fare_frame.grid(row=8, column=0, sticky="ew", pady=(0, 20))

fare_label = tk.Label(
    fare_frame,
    text="💰  FINAL FARE   Rs. --",
    font=("Segoe UI", 16, "bold"),
    bg=LIGHT_BLUE, fg=NAVY,
    justify="left", anchor="w"
)
fare_label.pack(fill="x", padx=20, pady=18)

# ============================================================
# ONBOARD PASSENGER SELECTION / WALLET
# ============================================================

wallet_title = section_title(
    content, "💳", "Passenger Wallet",
    "Select an onboard passenger to view or recharge their wallet."
)
wallet_title.grid(row=9, column=0, sticky="ew", pady=(0, 9))

wallet_frame = tk.Frame(
    content, bg=CARD,
    highlightbackground=BORDER, highlightthickness=1
)
wallet_frame.grid(row=10, column=0, sticky="ew", pady=(0, 20))
wallet_frame.columnconfigure(0, weight=1)
wallet_frame.columnconfigure(1, weight=1)

list_container = tk.Frame(wallet_frame, bg=CARD)
list_container.grid(row=0, column=0, sticky="nsew", padx=18, pady=15)

tk.Label(
    list_container,
    text="ONBOARD PASSENGERS",
    font=("Segoe UI", 9, "bold"),
    bg=CARD, fg=MUTED
).pack(anchor="w", pady=(0, 6))

onboard_list = tk.Listbox(
    list_container,
    height=4,
    font=("Segoe UI", 10),
    bg="#F8FAFC",
    fg=TEXT,
    selectbackground=BLUE,
    selectforeground="white",
    relief="flat",
    highlightbackground=BORDER,
    highlightthickness=1,
    activestyle="none"
)
onboard_list.pack(fill="both", expand=True)
onboard_list.bind("<<ListboxSelect>>", lambda event: update_selected_wallet())

wallet_controls = tk.Frame(wallet_frame, bg=CARD)
wallet_controls.grid(row=0, column=1, sticky="nsew", padx=18, pady=15)

tk.Label(
    wallet_controls,
    text="SELECTED WALLET",
    font=("Segoe UI", 9, "bold"),
    bg=CARD, fg=MUTED
).pack(anchor="w")

selected_wallet_label = tk.Label(
    wallet_controls,
    text="Select a passenger",
    font=("Segoe UI", 22, "bold"),
    bg=CARD, fg=NAVY
)
selected_wallet_label.pack(anchor="w", pady=(2, 10))

recharge_buttons = tk.Frame(wallet_controls, bg=CARD)
recharge_buttons.pack(fill="x")
recharge_buttons.columnconfigure(0, weight=1)
recharge_buttons.columnconfigure(1, weight=1)
recharge_buttons.columnconfigure(2, weight=1)

def selected_passenger_id():
    selection = onboard_list.curselection()

    if not selection:
        return None

    index = selection[0]
    ids = list(onboard_passengers.keys())

    if index >= len(ids):
        return None

    return ids[index]


def update_selected_wallet():
    pid = selected_passenger_id()

    if pid is None:
        selected_wallet_label.config(text="Select a passenger")
        return

    info = onboard_passengers[pid]["info"]
    balance = info.get("balance", 0)

    selected_wallet_label.config(
        text=f"Rs. {balance:.2f}"
    )


def recharge_wallet(amount):
    pid = selected_passenger_id()

    if pid is None:
        fare_label.config(
            text="⚠ Select an onboard passenger before recharging.",
            fg=AMBER
        )
        return

    info = onboard_passengers[pid]["info"]

    new_balance = info.get("balance", 0) + amount
    info["balance"] = new_balance
    passengers[str(pid)]["balance"] = new_balance

    with open("passengers.json", "w") as file:
        json.dump(passengers, file, indent=4)

    update_selected_wallet()
    update_passenger_display()

    # Restore selection after display refresh
    ids = list(onboard_passengers.keys())
    if pid in ids:
        onboard_list.selection_set(ids.index(pid))
        onboard_list.activate(ids.index(pid))

    fare_label.config(
        text=(
            f"💳 WALLET RECHARGED\n"
            f"{info['name']}  •  Added Rs. {amount:.2f}\n"
            f"New Balance: Rs. {new_balance:.2f}"
        ),
        fg=BLUE
    )


for col, amount in enumerate((50, 100, 500)):
    btn = make_button(
        recharge_buttons,
        f"+ Rs. {amount}",
        lambda value=amount: recharge_wallet(value),
        "#E8EEF7", "#DCE6F3", 10, 1, 9
    )
    btn.configure(fg=NAVY, activeforeground=NAVY)
    btn.grid(row=0, column=col, sticky="ew", padx=3)

# ============================================================
# TRANSACTION HISTORY
# ============================================================

history_title = section_title(
    content, "🧾", "Recent Transactions",
    "Latest successful payments."
)
history_title.grid(row=11, column=0, sticky="ew", pady=(0, 9))

history_frame = tk.Frame(
    content, bg=CARD,
    highlightbackground=BORDER, highlightthickness=1
)
history_frame.grid(row=12, column=0, sticky="ew", pady=(0, 20))

history_label = tk.Label(
    history_frame,
    text="No transactions yet",
    font=("Segoe UI", 10),
    bg=CARD, fg=MUTED,
    justify="left", anchor="w"
)
history_label.pack(fill="x", padx=20, pady=15)


def update_history():
    if not transaction_history:
        history_label.config(text="No transactions yet")
        return

    lines = []

    for t in transaction_history[-5:]:
        lines.append(
            f"{t['time']}   •   {t['name']} (ID {t['id']})   •   "
            f"{t['distance']:.1f} km   •   Rs. {t['fare']:.2f}   ✓ Paid"
        )

    history_label.config(text="\n".join(lines))

# ============================================================
# DAILY SUMMARY
# ============================================================

summary_title = section_title(
    content, "📊", "Daily Summary",
    "Live statistics for this SmartBus session."
)
summary_title.grid(row=13, column=0, sticky="ew", pady=(0, 9))

summary_frame = tk.Frame(
    content, bg=CARD,
    highlightbackground=BORDER, highlightthickness=1
)
summary_frame.grid(row=14, column=0, sticky="ew", pady=(0, 20))

summary_label = tk.Label(
    summary_frame,
    text="Passengers served: 0    •    Successful payments: 0    •    Failed payments: 0    •    Revenue: Rs. 0.00",
    font=("Segoe UI", 10, "bold"),
    bg=CARD, fg=NAVY
)
summary_label.pack(fill="x", padx=20, pady=16)


def update_summary():
    summary_label.config(
        text=(
            f"Passengers served: {successful_payments}    •    "
            f"Successful payments: {successful_payments}    •    "
            f"Failed payments: {failed_payments}    •    "
            f"Revenue: Rs. {total_revenue:.2f}"
        )
    )

# ============================================================
# FARE STRUCTURE
# ============================================================

fare_title = section_title(
    content, "📋", "Fare Structure",
    "Kathmandu Valley fare bands used by SmartBus."
)
fare_title.grid(row=15, column=0, sticky="ew", pady=(0, 9))

fare_structure = tk.Frame(
    content, bg=CARD,
    highlightbackground=BORDER, highlightthickness=1
)
fare_structure.grid(row=16, column=0, sticky="ew", pady=(0, 20))

fare_rows = [
    ("0 – 5 KM", "Rs. 24"),
    ("5 – 10 KM", "Rs. 33"),
    ("10 – 15 KM", "Rs. 39"),
    ("15 – 20 KM", "Rs. 44"),
    ("20+ KM", "Rs. 50")
]

for i, (distance_range, fare) in enumerate(fare_rows):
    row = tk.Frame(fare_structure, bg=CARD)
    row.pack(fill="x", padx=20, pady=(10 if i == 0 else 4, 0))

    tk.Label(
        row, text=distance_range,
        font=("Segoe UI", 10),
        bg=CARD, fg=TEXT
    ).pack(side="left")

    tk.Label(
        row, text=fare,
        font=("Segoe UI", 10, "bold"),
        bg=CARD, fg=NAVY
    ).pack(side="right")

tk.Label(
    fare_structure,
    text="Minimum payable fare: Rs. 20   •   Student: 45% OFF   •   Elder Citizen: 50% OFF",
    font=("Segoe UI", 9, "bold"),
    bg=LIGHT_BLUE, fg=BLUE
).pack(fill="x", padx=20, pady=14)

# ============================================================
# RESET
# ============================================================

def reset_bus():
    global distance
    global onboard_passengers
    global total_revenue
    global successful_payments
    global failed_payments
    global transaction_history

    distance = 0.0
    onboard_passengers = {}
    total_revenue = 0.0
    successful_payments = 0
    failed_payments = 0
    transaction_history = []

    distance_label.config(text="0.0 km")
    fare_label.config(
        text="💰  FINAL FARE   Rs. --",
        fg=NAVY
    )

    update_passenger_display()
    update_history()
    update_summary()


reset_button = make_button(
    content,
    "↻  RESET BUS",
    reset_bus,
    "#E8EEF7", "#DCE6F3", 18, 1, 10
)
reset_button.configure(fg=NAVY, activeforeground=NAVY)
reset_button.grid(row=17, column=0, pady=(0, 18))

tk.Label(
    content,
    text="SmartBus  •  Automated Distance-Based Fare Collection",
    font=("Segoe UI", 9),
    bg=BG, fg=MUTED
).grid(row=18, column=0, pady=(0, 15))

# ============================================================
# START
# ============================================================

window.mainloop()
