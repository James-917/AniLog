import customtkinter as ctk
import os
from tkinter import messagebox
from dbConnect import connect_to_dbusers

def login():
    username = entry_username.get()
    password = entry_password.get()

    # Connect to the database and verify login
    connection = connect_to_dbusers()
    if connection:
        cursor = connection.cursor()
        query = "SELECT id, username, name FROM tbaccount WHERE username=%s AND password=%s"
        cursor.execute(query, (username, password))
        result = cursor.fetchone()

        if result:
            user_id = result[0]
            user_name = result[2]
            messagebox.showinfo("Login Success", f"Welcome {user_name}!")
            proceed_to_home(user_id)
        else:
            messagebox.showwarning("Login Failed", "Incorrect username or password.")

        cursor.close()
        connection.close()

def proceed_to_home(user_id):
    app.destroy()
    os.system(f'python Home.py "{user_id}"')

def register():
    app.destroy()
    os.system("python Register.py")

def toggle_password():
    if entry_password.cget("show") == "":
        entry_password.configure(show="*")
    else:
        entry_password.configure(show="")


# UI Design ======================================================================================

# Set up the main application window
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
app = ctk.CTk()
app.geometry("400x400+10+10")
app.title("Login")


# Frame 1 (Top Header)
frame_header = ctk.CTkFrame(app, fg_color="black", corner_radius=0)
frame_header.pack( fill="x", side="top")

# Main frame for login form
frame_form = ctk.CTkFrame(app, width=500, height=500, corner_radius=10, )
frame_form.pack(expand=True, padx=20, pady=20)

# Form title
label_title = ctk.CTkLabel(frame_header, text="AniLog", font=("Bahnschrift", 24, "bold", ), fg_color="darkblue", corner_radius= 10)
label_title.pack(pady= 10)

# Username entry
entry_username = ctk.CTkEntry(frame_form, placeholder_text="Username", width=240)
entry_username.pack(pady=(30, 10))

# Password entry
entry_password = ctk.CTkEntry(frame_form, placeholder_text="Password", show="*", width=240)
entry_password.pack(pady=(10, 10))

# Frame for Show Password
frame_toggle = ctk.CTkFrame(frame_form, fg_color="transparent")
frame_toggle.pack(padx=20,pady=10, anchor="w")

# Label Show Password
label_show_password = ctk.CTkLabel(frame_toggle, text="Show Password", font=("Arial", 11))
label_show_password.pack(side="left", padx=5, pady=5)

# Toggle Switch
toggle_password_switch = ctk.CTkSwitch(frame_toggle, text="", command=toggle_password)
toggle_password_switch.pack(side="left")

# Register and Login buttons
frame_buttons = ctk.CTkFrame(frame_form, fg_color="transparent")
frame_buttons.pack(pady=20,padx=20)

button_register = ctk.CTkButton(frame_buttons, text="Register", font=('Arial', 12, 'bold'), width=100, command=register)
button_register.grid(row=0, column=0, padx=10)

label_or = ctk.CTkLabel(frame_buttons, text="or", font=("Arial", 12))
label_or.grid(row=0, column=1)

button_login = ctk.CTkButton(frame_buttons, text="Login", font=('Arial', 12, 'bold'), width=100, command=login)
button_login.grid(row=0, column=2, padx=10)

# Run the application
app.mainloop()
