import pymysql
import customtkinter as ctk
import os
import sys
from tkinter import messagebox
from PIL import Image, ImageTk
from customtkinter import CTkFrame
from dbConnect import connect_to_dbusers
from dbConnect import connect_to_dbanime

# Get the user's username and name passed from the login page
if len(sys.argv) > 1:
    user_id = int(sys.argv[1])  # Accept the user_id from the command line
else:
    user_id = None  # Default value

# Print feedback about what has been received
if user_id:
    # Fetch user details using user_id
    connection = connect_to_dbusers()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT username, name FROM tbaccount WHERE id = %s", (user_id,))
        result = cursor.fetchone()

        if result:
            user_username = result[0]
            user_name = result[1]

        else:
            print("No user found with the provided ID.")
        connection.close()
else:
    print("No user ID provided.")

# Function to handle "+" button clicks
def add_title(title, user_name, user_id):
    try:
        # Ensure user_name and user_id are available
        if not user_name or user_name == "Guest":
            messagebox.showerror("Error", "User not logged in.")
            return

        # Connect to the dbusers database
        connection = connect_to_dbusers()
        if not connection:
            messagebox.showerror("Error", "Failed to connect to dbusers.")
            return

        with connection.cursor() as cursor:
            # Check if the title already exists in the user's list
            query = "SELECT * FROM tblist WHERE id = %s AND Title = %s"
            cursor.execute(query, (user_id, title))
            existing_entry = cursor.fetchone()

            if existing_entry:
                # Title already exists in the list, show a message
                messagebox.showinfo("Info", f"'{title}' is already in your list!")
            else:
                # Insert the new title into tblist
                query = "INSERT INTO tblist (id, name, Title, score, status, progress) VALUES (%s, %s, %s, %s, %s, %s)"
                cursor.execute(query, (user_id, user_name, title, 0, "Plan to Watch", 0))
                connection.commit()

                messagebox.showinfo("Success", f"'{title}' has been added to {user_name}'s list!")

    except pymysql.MySQLError as e:
        messagebox.showerror("Database Error", f"Error inserting data: {e}")
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        if connection:
            connection.close()

# Function to navigate back to home
def proceed_to_home(user_id):
    # Check if user_id is available before calling the function
    if user_id is None:
        print("Error: user_id is missing!")
        return

    # Fetch user_id and pass it to home.py
    app.destroy()
    os.system(f'python home.py "{user_id}"')  # Pass user_id to home.py

# Function to fetch and resize an image from a URL
def fetch_image(file_path, max_width=50, max_height=125):
    try:
        # Construct the full path to the image
        full_path = os.path.join(os.getcwd(), file_path)

        # Check if the file exists
        if not os.path.exists(full_path):
            print(f"Image file not found: {full_path}")
            return None

        # Open the image
        img = Image.open(full_path)

        # Get original image dimensions
        original_width, original_height = img.size

        # Calculate the scaling factor to maintain aspect ratio
        width_ratio = max_width / original_width
        height_ratio = max_height / original_height
        scale_factor = min(width_ratio, height_ratio)

        # Calculate new dimensions
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)

        # Resize the image to the new dimensions
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"Error loading image: {e}")
        return None

# Function to search for an anime title
def search_anime():
    title_to_search = search_entry.get().strip()
    if not title_to_search:
        result_label.configure(text="Please enter a title to search.")
        return

    # Clear the previous search results
    for widget in result_canvas_frame.winfo_children():
        widget.destroy()

    connection = connect_to_dbanime()
    if connection:
        try:
            with connection.cursor() as cursor:
                # Query to search for titles and images containing the input string
                query = "SELECT Title, ImageURL FROM tbanime WHERE Title LIKE %s"
                cursor.execute(query, (f"%{title_to_search}%",))
                results = cursor.fetchall()

                if results:
                    for row in results:
                        title, image_url = row

                        # Create a frame for each result
                        result_item = ctk.CTkFrame(result_canvas_frame, width=600, )
                        result_item.pack(fill="x", pady=5, expand=True)

                        # Fetch and display the image
                        img = fetch_image(image_url)
                        if img:
                            img_label = ctk.CTkLabel(result_item, image=img, text="")
                            img_label.image = img  # Keep a reference to avoid garbage collection
                            img_label.pack(side="left", padx=5, pady=5)

                        # Display the title
                        title_label = ctk.CTkLabel(result_item, text=title, anchor="w", width=200)
                        title_label.pack(side="left", padx=5, pady=5)

                        # Add the "+" button
                        add_button = ctk.CTkButton(
                            result_item,
                            text="+",
                            width=30,
                            command=lambda t=title, un=user_name, uid=user_id: add_title(t, un, uid)  # Pass both user_name and user_id
                        )
                        add_button.pack(side="right", padx=5)
                else:
                    result_label.configure(text="No titles found.")
        except pymysql.MySQLError as e:
            result_label.configure(text=f"Error: {e}")
        finally:
            connection.close()
    else:
        result_label.configure(text="Failed to connect to the database.")

# Update the scrollable region whenever the content changes
def update_scroll_region(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

# UI Design ======================================================================================

# UI setup using customtkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
app = ctk.CTk()
app.geometry("600x800+10+10")
app.title("Anime Search")

# Frame
frame1 = CTkFrame(app, fg_color="black", corner_radius=0)
frame1.pack(fill="x")

frame1.columnconfigure(0, weight=0)
frame1.columnconfigure(1, weight=0)

# Input label and entry box
label_title = ctk.CTkLabel(frame1, text="  AniLog  ", font=("Bahnschrift", 24, "bold", ), fg_color="darkblue", corner_radius=10)
label_title.grid(row=0, column=1, padx=(125,0), pady=10, sticky='')

# Back button
back_button = ctk.CTkButton(frame1, text="Back", command=lambda: proceed_to_home(user_id), width=80)
back_button.grid(row=0, column=0, padx=10, pady=10, sticky='nw')

# Search Entry
search_entry = ctk.CTkEntry(app, width=400)
search_entry.pack(pady=10)

# Search button
search_button = ctk.CTkButton(app, text="Search", command=search_anime)
search_button.pack(pady=10)

# Label for additional messages
result_label = ctk.CTkLabel(app, text="")
result_label.pack(pady=5)

# Frame to display search results with scrollable canvas
canvas = ctk.CTkCanvas(app,bg="#282424", highlightthickness=0)
canvas.pack(side="left",fill="both", expand=True, padx=10, pady=10)

# Scrollbar for the canvas
scrollbar = ctk.CTkScrollbar(app, orientation="vertical", command=canvas.yview)
scrollbar.pack(side="right", fill="y")
canvas.configure(yscrollcommand=scrollbar.set)

# Frame inside canvas to hold the results
result_canvas_frame = ctk.CTkFrame(canvas, fg_color='transparent')
canvas_window = canvas.create_window((0, 0), window=result_canvas_frame, anchor="nw",width=canvas.winfo_width())

# Bind events to adjust main_frame width
result_canvas_frame.bind("<Configure>", update_scroll_region)
canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

# Configure main_frame to expand
result_canvas_frame.grid_columnconfigure(0, weight=1)
result_canvas_frame.grid_rowconfigure(0, weight=1)


app.mainloop()
