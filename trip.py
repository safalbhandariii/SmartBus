passenger_id = 101

entry_distance = float(input("Enter entry distance: "))

print("\nPassenger", passenger_id, "boarded.")
print("Entry distance:", entry_distance, "km")

exit_distance = float(input("\nEnter exit distance: "))

print("\nPassenger", passenger_id, "exited.")
print("Exit distance:", exit_distance, "km")

distance_travelled = exit_distance - entry_distance

print("\nDistance travelled:", distance_travelled, "km")