
import tkinter as tk

window = tk.Tk()

window.title("SmartBus")

window.geometry("500x400")

title = tk.Label(
    window,
    text="SMARTBUS",
    font=("Arial", 24)
)

title.pack(pady=30)

message = tk.Label(
    window,
    text="Automated Bus Fare System",
    font=("Arial", 14)
)

message.pack()

window.mainloop()

