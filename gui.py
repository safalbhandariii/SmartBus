import tkinter as tk
import cv2
import json

distance = 0.0
speed = 30

passenger_id = None
entry_distance = None
passenger_info = None

with open("passengers.json", "r") as file:
    passengers = json.load(file)    
    
    
# -----------------------------
# FACE RECOGNITION
# -----------------------------

recognizer = cv2.face.LBPHFaceRecognizer_create()

recognizer.read("trainer.yml")

face_detector = cv2.CascadeClassifier(
    "haarcascade_frontalface_default.xml"
)

window = tk.Tk()

window.title("SmartBus - Automated Fare System")

window.geometry("900x700")

window.resizable(True, True)


# -----------------------------
# TITLE
# -----------------------------

title = tk.Label(
    window,
    text="🚌 SMARTBUS",
    font=("Arial", 28, "bold")
)

title.pack(pady=8)

subtitle = tk.Label(
    window,
    text="Automated Bus Fare Collection",
    font=("Arial", 14)
)

subtitle.pack()


# -----------------------------
# BUS INFORMATION
# -----------------------------

bus_frame = tk.LabelFrame(
    window,
    text="Bus Status",
    font=("Arial", 14, "bold"),
    padx=20,
    pady=15
)

bus_frame.pack(
    fill="x",
    padx=30,
    pady=8
)

distance_label = tk.Label(
    bus_frame,
    text="Distance: 0.0 km",
    font=("Arial", 16)
)

distance_label.pack(pady=5)

speed_label = tk.Label(
    bus_frame,
    text="Speed: 30 km/h",
    font=("Arial", 16)
)

speed_label.pack(pady=5)


# -----------------------------
# PASSENGER INFORMATION
# -----------------------------

passenger_frame = tk.LabelFrame(
    window,
    text="Passenger",
    font=("Arial", 14, "bold"),
    padx=20,
    pady=15
)

passenger_frame.pack(
    fill="x",
    padx=30,
    pady=5
)

passenger_label = tk.Label(
    passenger_frame,
    text="No passenger currently onboard",
    font=("Arial", 15)
)

passenger_label.pack(pady=10)



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
            "SmartBus - Board",
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


def board_passenger():

    global passenger_id
    global entry_distance
    global passenger_info

    if passenger_id is not None:

        passenger_label.config(
            text="A passenger is already onboard."
        )

        return

    detected_id = scan_face()

    if detected_id is None:

        passenger_label.config(
            text="No passenger recognized."
        )

        return

    if str(detected_id) not in passengers:

        passenger_label.config(
            text="Passenger is not registered."
        )

        return

    passenger_id = detected_id

    passenger_info = passengers[
        str(passenger_id)
    ]

    entry_distance = distance

    passenger_label.config(
        text=(
            f"ID: {passenger_id} | "
            f"Name: {passenger_info['name']} | "
            f"Type: {passenger_info['type']} | "
            f"Entry: {entry_distance:.1f} km"
        )
    )
    
    

def exit_passenger():

    global passenger_id
    global entry_distance
    global passenger_info

    # -----------------------------
    # CHECK PASSENGER
    # -----------------------------

    if passenger_id is None:

        passenger_label.config(
            text="No passenger is currently onboard."
        )

        return

    # -----------------------------
    # SCAN FACE
    # -----------------------------

    detected_id = scan_face()

    if detected_id != passenger_id:

        passenger_label.config(
            text="Wrong passenger or face not recognized."
        )

        return

    # -----------------------------
    # CALCULATE DISTANCE
    # -----------------------------

    exit_distance = distance

    distance_travelled = (
        exit_distance - entry_distance
    )

    # -----------------------------
    # KATHMANDU VALLEY FARE
    # -----------------------------

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

    # -----------------------------
    # APPLY DISCOUNT
    # -----------------------------

    discount = (
        base_fare *
        passenger_info["discount"]
    )

    calculated_fare = (
        base_fare - discount
    )

    # Minimum payable fare
    final_fare = max(
        calculated_fare,
        20
    )
    actual_discount = base_fare - final_fare

    # -----------------------------
    # DISPLAY PASSENGER
    # -----------------------------

    passenger_label.config(
        text=(
            f"Passenger: {passenger_info['name']} | "
            f"ID: {passenger_id} | "
            f"Type: {passenger_info['type']} | "
            f"Distance: {distance_travelled:.1f} km"
        )
    )

    # -----------------------------
    # DISPLAY FARE
    # -----------------------------

    fare_label.config(
        text=(
            f"💰 FINAL FARE: Rs. {final_fare:.2f}\n"
            f"Base: Rs. {base_fare:.2f} | "
            f"Actual Discount: Rs. {actual_discount:.2f}"
        )
    )

    # -----------------------------
    # CLEAR PASSENGER
    # -----------------------------

    passenger_id = None
    entry_distance = None
    passenger_info = None
    
    passenger_label.config(
    text="No passenger currently onboard"
)


# -----------------------------
# BUTTONS
# -----------------------------

button_frame = tk.Frame(window)

button_frame.pack(pady=8)


board_button = tk.Button(
    button_frame,
    text="🟢 BOARD PASSENGER",
    font=("Arial", 14, "bold"),
    width=20,
    height=2,
    command=board_passenger
)

board_button.grid(
    row=0,
    column=0,
    padx=10
)

exit_button = tk.Button(
    button_frame,
    text="🔴 EXIT PASSENGER",
    font=("Arial", 14, "bold"),
    width=20,
    height=2,
    command=exit_passenger
)



exit_button.grid(
    row=0,
    column=1,
    padx=10
)


# -----------------------------
# DISTANCE BUTTONS
# -----------------------------

move_frame = tk.Frame(window)

move_frame.pack(pady=3)


def move_half():
    global distance

    distance += 0.5

    distance_label.config(
        text=f"Distance: {distance:.1f} km"
    )


def move_one():
    global distance

    distance += 1.0

    distance_label.config(
        text=f"Distance: {distance:.1f} km"
    )



move_half_button = tk.Button(
    move_frame,
    text="+ 0.5 KM",
    font=("Arial", 12),
    width=15,
    command=move_half
)

move_half_button.grid(
    row=0,
    column=0,
    padx=5
)


move_one_button = tk.Button(
    move_frame,
    text="+ 1 KM",
    font=("Arial", 12),
    width=15,
    command=move_one
)

move_one_button.grid(
    row=0,
    column=1,
    padx=5
)


# -----------------------------
# FARE
# -----------------------------

fare_label = tk.Label(
    window,
    text="Fare: --",
    font=("Arial", 22, "bold")
)

fare_label.pack(pady=8)


# -----------------------------
# START GUI
# -----------------------------

window.mainloop()

