
import cv2
import os

passenger_id = input("Enter passenger ID: ")
name = input("Enter passenger name: ")

os.makedirs("faces", exist_ok=True)

camera = cv2.VideoCapture(0)

face_detector = cv2.CascadeClassifier(
    "haarcascade_frontalface_default.xml"
)

sample_count = 0

print("\nLook at the camera.")
print("The system will capture 20 face samples automatically.")
print("Press Q to cancel.\n")

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

        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )

        if sample_count < 20:

            face = gray[y:y+h, x:x+w]

            sample_count += 1

            filename = f"faces/{passenger_id}_{sample_count}.jpg"

            cv2.imwrite(filename, face)

            print(f"Captured sample {sample_count}/20")

        cv2.putText(
            frame,
            f"Samples: {sample_count}/20",
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

    cv2.imshow("SmartBus - Registration", frame)

    if sample_count >= 20:
        print("\nRegistration completed!")
        print(f"Passenger ID: {passenger_id}")
        print(f"Name: {name}")
        break

    if cv2.waitKey(100) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
