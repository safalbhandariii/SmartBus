
import cv2
import json


# -----------------------------
# LOAD PASSENGER DATABASE
# -----------------------------

with open("passengers.json", "r") as file:
    passengers = json.load(file)




# -----------------------------
# BUS INFORMATION
# -----------------------------

distance = 0.0
speed = 30

passenger_id = None
entry_distance = None
passenger_info = None


# -----------------------------
# FACE RECOGNITION
# -----------------------------

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("trainer.yml")

face_detector = cv2.CascadeClassifier(
    "haarcascade_frontalface_default.xml"
)


def scan_face():

    camera = cv2.VideoCapture(0)

    print("\nOpening camera...")
    print("Look at the camera.")
    print("Press Q to cancel.")

    detected_id = None

    while True:

        success, frame = camera.read()

        if not success:
            print("Could not access camera")
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
                text = f"Passenger {face_id}"
                detected_id = face_id
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
                (x, y-10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

        cv2.imshow("SmartBus - Face Scanner", frame)

        key = cv2.waitKey(1) & 0xFF

        if detected_id is not None:
            break

        if key == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

    return detected_id


# -----------------------------
# MAIN SMARTBUS PROGRAM
# -----------------------------

while True:

    print("\n================================")
    print("          SMARTBUS")
    print("================================")

    print("Current distance:", distance, "km")
    print("Current speed:", speed, "km/h")

    if passenger_id is None:
        print("Passenger: None")
    else:
        print("Passenger:", passenger_id)
        print("Entry distance:", entry_distance, "km")

    print("\n1. Move 0.5 km")
    print("2. Move 1 km")
    print("3. Scan passenger / Board")
    print("4. Scan passenger / Exit")
    print("5. Reset")
    print("6. Quit")

    choice = input("\nEnter choice: ")

    # -----------------------------
    # MOVE BUS
    # -----------------------------

    if choice == "1":

        distance += 0.5

    elif choice == "2":

        distance += 1.0

    # -----------------------------
    # BOARD PASSENGER
    # -----------------------------

    elif choice == "3":

        if passenger_id is not None:

            print("A passenger is already on the bus.")

        else:

            detected_id = scan_face()

            
            if detected_id is not None:

                if str(detected_id) in passengers:

                    passenger_id = detected_id
                    passenger_info = passengers[str(passenger_id)]

                    entry_distance = distance

                    print("\n===== PASSENGER FOUND =====")
                    print("Passenger ID:", passenger_id)
                    print("Name:", passenger_info["name"])
                    print("Type:", passenger_info["type"])
                    print(
                        "Discount:",
                        passenger_info["discount"] * 100,
                        "%"
                    )

                    print("\nPassenger boarded.")
                    print("Entry distance:", entry_distance, "km")

                else:

                    print("Passenger is not registered.")



    # -----------------------------
    # EXIT PASSENGER
    # -----------------------------

    elif choice == "4":

        if passenger_id is None:

            print("No passenger is currently on the bus.")

        else:

            detected_id = scan_face()

            if detected_id == passenger_id:

                exit_distance = distance

                print("\nPassenger", passenger_id, "recognized!")
                print("Passenger exited.")
                print("Exit distance:", exit_distance, "km")

                distance_travelled = (
                    exit_distance - entry_distance
                )

                print(
                    "Distance travelled:",
                    distance_travelled,
                    "km"
                )

                # -----------------------------
                # FARE CALCULATION
                # -----------------------------

                rate = 5

                base_fare = distance_travelled * rate

                discount = base_fare * passenger_info["discount"]

                final_fare = base_fare - discount

                print("\n===== SMARTBUS FARE =====")
                print("Passenger:", passenger_info["name"])
                print("Type:", passenger_info["type"])
                print("Distance:", distance_travelled, "km")
                print("Base fare: Rs.", base_fare)
                print(
                    "Discount:",
                    passenger_info["discount"] * 100,
                    "%"
                )
                print("Discount amount: Rs.", discount)
                print("FINAL FARE: Rs.", final_fare)

                passenger_id = None
                entry_distance = None
                passenger_info = None
              


    # -----------------------------
    # RESET
    # -----------------------------

    elif choice == "5":

        distance = 0.0
        passenger_id = None
        entry_distance = None

        print("SmartBus reset.")

    # -----------------------------
    # QUIT
    # -----------------------------

    elif choice == "6":

        print("SmartBus closed.")
        break

    else:

        print("Invalid choice.")

