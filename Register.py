import customtkinter as ctk
import pymysql
import os
from tkinter import messagebox
from dbConnect import connect_to_dbusers

# Function to check if username exists
def is_username_taken(username):
    connection = connect_to_dbusers()
    if connection:
        cursor = connection.cursor()
        query = "SELECT * FROM tbaccount WHERE username=%s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return result is not None
    return False

# Function to save user data to the database
def save_registration():
    name = entry_name.get()
    username = entry_username.get()
    password = entry_password.get()
    confirm_password = entry_confirm_password.get()

    # Validate input
    if not name or not username or not password or not confirm_password:
        messagebox.showwarning("Input Error", "All fields are required!")
        return

    if password != confirm_password:
        messagebox.showerror("Password Error", "Passwords do not match!")
        return

    if is_username_taken(username):
        messagebox.showerror("Username Error", "Username already exists!")
        return

    # Save to database
    connection = connect_to_dbusers()
    if connection:
        try:
            cursor = connection.cursor()
            query = "INSERT INTO tbaccount (name, username, password) VALUES (%s, %s, %s)"
            cursor.execute(query, (name, username, password))
            connection.commit()
            messagebox.showinfo("Success", "Registration successful!")
            cursor.close()
            connection.close()
        except pymysql.MySQLError as e:
            messagebox.showerror("Database Error", f"Error saving data: {e}")

# Function to go back to the login page
def go_back():
    app.destroy()
    os.system("python Login.py")

# UI Design ======================================================================================

# Set up main application Window
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
app = ctk.CTk()
app.title("Register")
app.geometry("450x500+10+10")

# Frame 1 (Top Header)
frame_header = ctk.CTkFrame(app, fg_color="black", corner_radius=0)
frame_header.pack( fill="x", side="top")

# Main frame for register form
frame_form = ctk.CTkFrame(app, width=500, height=500, corner_radius=10)
frame_form.pack(expand=True, padx=20, pady=20)

# Title
label_title = ctk.CTkLabel(frame_header, text="YOUR\nANIME LIST", font=("Bahnschrift", 24, "bold", ), fg_color="darkblue", corner_radius= 10)
label_title.pack(pady=20)

# Name Entry with Placeholder
entry_name = ctk.CTkEntry(frame_form, width=300, placeholder_text="Name")
entry_name.pack(pady=(30,10))

# Username Entry with Placeholder
entry_username = ctk.CTkEntry(frame_form, width=300, placeholder_text="Username")
entry_username.pack(pady=10)

# Password Entry with Placeholder
entry_password = ctk.CTkEntry(frame_form, width=300, show="", placeholder_text="Password")
entry_password.pack(pady=10)

# Confirm Password Entry with Placeholder
entry_confirm_password = ctk.CTkEntry(frame_form, width=300, show="", placeholder_text="Confirm Password")
entry_confirm_password.pack(pady=10)

# Register and Login buttons
frame_buttons = ctk.CTkFrame(frame_form, fg_color="transparent")
frame_buttons.pack(pady=(20, 20),padx=(20,20))

# Back Button
button_back = ctk.CTkButton(frame_buttons, text="BACK", width=100, command=go_back)
button_back.pack(pady=(20, 5), side="left", padx=30)

# Save Button
button_save = ctk.CTkButton(frame_buttons, text="SAVE", width=100, command=save_registration)
button_save.pack(pady=(20, 5), side="right", padx=30)

# Run the app
app.mainloop()
