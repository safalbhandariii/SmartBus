distance = 0.0
speed = 30

while True:
    print("\n===== SMARTBUS =====")
    print("Current distance:", distance, "km")
    print("Current speed:", speed, "km/h")

    print("\n1. Move 0.5 km")
    print("2. Move 1 km")
    print("3. Reset")
    print("4. Exit")

    choice = input("Enter choice: ")

    if choice == "1":
        distance += 0.5

    elif choice == "2":
        distance += 1.0

    elif choice == "3":
        distance = 0.0

    elif choice == "4":
        break

    else:
        print("Invalid choice")