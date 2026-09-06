
import cv2
import json
import os

# -----------------------------
# LOAD PASSENGER DATABASE
# -----------------------------

if os.path.exists("passengers.json"):

    with open("passengers.json", "r") as file:
        passengers = json.load(file)

else:

    passengers = {}


# -----------------------------
# PASSENGER INFORMATION
# -----------------------------

passenger_id = input("Enter passenger ID: ")
name = input("Enter passenger name: ")

print("\nPassenger types:")
print("1. Regular")
print("2. Student")
print("3. Senior")

choice = input("Choose passenger type: ")


if choice == "1":

    passenger_type = "regular"
    discount = 0.00

elif choice == "2":

    passenger_type = "student"
    discount = 0.45

elif choice == "3":

    passenger_type = "senior"
    discount = 0.50

else:

    print("Invalid passenger type.")
    exit()


# -----------------------------
# CREATE FACE FOLDER
# -----------------------------

os.makedirs("faces", exist_ok=True)


# -----------------------------
# CAMERA
# -----------------------------

camera = cv2.VideoCapture(0)

face_detector = cv2.CascadeClassifier(
    "haarcascade_frontalface_default.xml"
)

print("\nLook at the camera.")
print("Press SPACE to capture.")
print("Press Q to cancel.")


while True:

    success, frame = camera.read()

    if not success:

        print("Could not access camera")
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

        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            "Face detected",
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

    cv2.imshow(
        "SmartBus - Registration",
        frame
    )

    key = cv2.waitKey(1) & 0xFF

    if key == ord(" "):

        if len(faces) == 1:

            x, y, w, h = faces[0]

            face = gray[y:y+h, x:x+w]

            filename = f"faces/{passenger_id}.jpg"

            cv2.imwrite(
                filename,
                face
            )

            print(
                "\nFace saved successfully!"
            )

            break

        else:

            print(
                "Please make sure exactly one face is visible."
            )

    elif key == ord("q"):

        break


camera.release()
cv2.destroyAllWindows()


# -----------------------------
# SAVE PASSENGER INFORMATION
# -----------------------------

if os.path.exists(
    f"faces/{passenger_id}.jpg"
):

    passengers[passenger_id] = {
        "name": name,
        "type": passenger_type,
        "discount": discount
    }

    with open(
        "passengers.json",
        "w"
    ) as file:

        json.dump(
            passengers,
            file,
            indent=4
        )

    print("\n==============================")
    print("Passenger registered!")
    print("==============================")
    print("ID:", passenger_id)
    print("Name:", name)
    print("Type:", passenger_type)
    print(
        "Discount:",
        discount * 100,
        "%"
    )

