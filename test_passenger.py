from passengers import passengers

passenger_id = 101

if passenger_id in passengers:

    passenger = passengers[passenger_id]

    print("Passenger ID:", passenger_id)
    print("Name:", passenger["name"])
    print("Type:", passenger["type"])
    print("Discount:", passenger["discount"] * 100, "%")

else:

    print("Passenger not found")