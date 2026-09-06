distance = float(input("Enter distance travelled (km): "))
passenger_type = input("Enter passenger type: ")

rate = 5

base_fare = distance * rate

if passenger_type.lower() == "student":
    discount = base_fare * 0.10

elif passenger_type.lower() == "senior":
    discount = base_fare * 0.20

else:
    discount = 0

final_fare = base_fare - discount

print("\n===== SMARTBUS FARE =====")
print("Distance:", distance, "km")
print("Base fare: Rs.", base_fare)
print("Discount: Rs.", discount)
print("Final fare: Rs.", final_fare)