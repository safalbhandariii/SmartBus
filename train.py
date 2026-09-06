
import cv2
import os
import numpy as np

recognizer = cv2.face.LBPHFaceRecognizer_create()

faces = []
ids = []

folder = "faces"

# -----------------------------
# LOAD ALL FACE IMAGES
# -----------------------------

for filename in os.listdir(folder):

    if filename.endswith(".jpg"):

        image_path = os.path.join(
            folder,
            filename
        )

        image = cv2.imread(
            image_path,
            cv2.IMREAD_GRAYSCALE
        )

        if image is None:
            continue

        # Get passenger ID from filename
        passenger_id = int(
            filename.split(".")[0]
        )

        faces.append(image)
        ids.append(passenger_id)

        print(
            "Loaded face:",
            passenger_id
        )


# -----------------------------
# CHECK FACE DATA
# -----------------------------

if len(faces) == 0:

    print("No face images found.")
    exit()


# -----------------------------
# TRAIN MODEL
# -----------------------------

recognizer.train(
    faces,
    np.array(ids)
)

recognizer.write(
    "trainer.yml"
)


# -----------------------------
# RESULT
# -----------------------------

print("\n==============================")
print("Training completed successfully!")
print("==============================")
print("Number of face samples:", len(faces))
print("Passenger IDs:", ids)
print("Created trainer.yml")

