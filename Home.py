# Import Libraries ======================================================================================
import customtkinter as ctk
import os
import sys
import pymysql
from PIL import Image, ImageTk
from tkinter import messagebox
from dbConnect import connect_to_dbusers
from dbConnect import connect_to_dbanime

anime_entries = []
displayed_entries = []
is_ascending = True
current_sort_by = "Alphabet"
current_filter = "All"
filtered_entries = []
last_clicked_button = None

# Functions ======================================================================================
# Get the user_id passed from the login page
try:
    user_id = int(sys.argv[1])  # Expects an integer
except ValueError:
    print("Error: user_id must be an integer.")
    sys.exit(1)

def fetch_user_details(user_id):
    try:
        connection = connect_to_dbusers()
        if not connection:
            messagebox.showerror("Error", "Failed to connect to the database.")
            return None, None

        with connection.cursor() as cursor:
            query = "SELECT username, name FROM tbaccount WHERE id = %s"
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()

        if user:
            return user[0], user[1]  # Return username and name
        else:
            return None, None
    except pymysql.MySQLError as e:
        messagebox.showerror("Database Error", f"Error fetching user details: {e}")
        return None, None
    finally:
        if connection:
            connection.close()

# Get username and name using `user_id`
user_username, user_name = fetch_user_details(user_id)

def logout():
    app.destroy()
    os.system(f'python Login.py')

def go_search():
    app.destroy()
    os.system(f'python Search.py "{user_id}"')
    # Pass `user_id` to Search.py

def fetch_anime_entries():
    global anime_entries  # Declare anime_entries as a global variable
    try:
        conn_users = connect_to_dbusers()  # Connect to dbusers for anime entries
        cursor_users = conn_users.cursor()

        # Fetch anime entries from tblist for the given user_id, including ImageURL and id_entry
        query = """
        SELECT l.id_entry, l.id AS user_id, l.name AS user_name, l.Title, l.score, l.status, l.progress, a.episode, a.ImageURL
        FROM dbusers.tblist l
        JOIN dbanime.tbanime a ON l.Title = a.Title
        WHERE l.id = %s
        """
        cursor_users.execute(query, (user_id,))
        results = cursor_users.fetchall()

        # Convert results to a list of dictionaries
        anime_entries.clear()  # Clear previous entries
        for row in results:
            anime_entry = {
                'id_entry': row[0],   # Add id_entry here
                'user_id': row[1],
                'username': row[2],
                'Title': row[3],
                'score': row[4],
                'status': row[5],
                'progress': row[6],
                'episode': row[7],   # Refers to the 'episode' column
                'ImageURL': row[8],   # Fetch the 'ImageURL' column from tbanime
            }
            anime_entries.append(anime_entry)

        if not anime_entries:
            messagebox.showinfo("No Entries", "No anime entries found for this user.")

        return anime_entries
    except pymysql.MySQLError as e:
        messagebox.showerror("Database Error", f"Error fetching anime entries: {e}")
        return []
    finally:
        if conn_users:
            conn_users.close()

def increment_progress(id_entry):
    global filtered_entries  # Use filtered_entries to maintain the current view
    try:
        conn_users = connect_to_dbusers()
        conn_anime = connect_to_dbanime()
        cursor_users = conn_users.cursor()

        # Fetch the current progress and max episode for this anime
        query_fetch = """
        SELECT l.progress, a.episode
        FROM tblist l
        JOIN dbanime.tbanime a ON l.Title = a.Title
        WHERE l.id_entry = %s
        """
        cursor_users.execute(query_fetch, (id_entry,))
        result = cursor_users.fetchone()

        if not result:
            messagebox.showerror("Error", "Anime entry not found.")
            return

        current_progress, max_episode = result

        if current_progress >= max_episode:
            messagebox.showinfo("Limit Reached", "You have already reached the maximum number of episodes.")
            return

        # Update progress if it is less than max episode
        query_update = """
        UPDATE tblist
        SET progress = progress + 1
        WHERE id_entry = %s
        """
        cursor_users.execute(query_update, (id_entry,))
        conn_users.commit()

        messagebox.showinfo("Success", "Progress updated successfully!")

        # Update the specific entry in filtered_entries
        for anime in filtered_entries:
            if anime['id_entry'] == id_entry:
                anime['progress'] = current_progress + 1
                break

        # Refresh the display with the filtered entries
        display_anime_entries(filtered_entries)
    except pymysql.MySQLError as e:
        messagebox.showerror("Database Error", f"Error updating progress: {e}")
    finally:
        if conn_users:
            conn_users.close()
        if conn_anime:
            conn_anime.close()

def edit_anime_entry(anime):
    """Open a mini window to edit an anime entry."""
    mini_window = ctk.CTkToplevel()
    mini_window.title(f"Edit {anime['Title']} Entry")  # Updated title
    mini_window.geometry("600x320+20+20")

    top_frame = ctk.CTkFrame(mini_window, fg_color="black", corner_radius=0)
    top_frame.pack(fill="x", side="top")

    mini_frame = ctk.CTkFrame(mini_window)
    mini_frame.pack(padx=20, pady=20, fill="both")
    mini_frame.columnconfigure(0, weight=1)
    mini_frame.columnconfigure(1, weight=0)
    mini_frame.rowconfigure(0, weight=1)
    mini_frame.rowconfigure(1, weight=0)

    label_title2 = ctk.CTkLabel(top_frame, text="  AniLog  ", font=("Bahnschrift", 24, "bold"),
                                fg_color="darkgreen",
                                corner_radius=10)
    label_title2.pack(padx=10, pady=10)

    # Set the mini window to always appear on top
    mini_window.attributes("-topmost", True)

    # Use the correct field name 'episode' for max_episode
    max_episode = anime['episode']  # Corrected from 'episodes'

    # Progress Label
    label_progress = ctk.CTkLabel(mini_frame, text="Progress:", font=("Arial", 12, "bold"))
    label_progress.grid(column=0, row=0, pady=20, padx=5, columnspan=2)

    # Display the Max Episode as a label
    label_max_episode = ctk.CTkLabel(mini_frame, text=f" / {max_episode}")
    label_max_episode.grid(column=1, row=1, pady=(0, 10), padx=(0, 80), sticky='w')

    # Create an entry box for progress (editable)
    entry_progress = ctk.CTkEntry(mini_frame, width=50)
    entry_progress.insert(0, str(anime['progress']))  # Set the default progress value
    entry_progress.grid(column=0, row=1, pady=(0, 10), padx=5, sticky='e')

    # Validate Progress to not exceed max episode (this could be done on saving the changes)
    def validate_progress():
        try:
            progress_value = int(entry_progress.get())
            if progress_value > max_episode:
                messagebox.showerror("Error", f"Progress cannot exceed the max episode: {max_episode}")
                entry_progress.delete(0, 'end')
                entry_progress.insert(0, str(anime['progress']))  # Reset to old progress value
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for progress.")

    # Score Label
    label_score = ctk.CTkLabel(mini_frame, text="Score:", font=("Arial", 12, "bold"))
    label_score.grid(column=2, row=0, pady=20, padx=5, )
    score_options = [str(i) for i in range(1, 11)]  # Dropdown options from 1 to 10

    # Score Dropdown
    dropdown_score = ctk.CTkOptionMenu(mini_frame, values=score_options)
    dropdown_score.set(str(anime['score']))  # Default value as string
    dropdown_score.grid(column=2, row=1, pady=(0, 10), padx=5, )

    # Status Label
    label_status = ctk.CTkLabel(mini_frame, text="Status:", font=("Arial", 12, "bold"))
    label_status.grid(column=3, row=0, pady=20, padx=5, )
    status_options = ["Watching", "Completed", "On Hold", "Dropped", "Plan to Watch"]

    # Status Dropdown
    dropdown_status = ctk.CTkOptionMenu(mini_frame, values=status_options)
    dropdown_status.set(anime['status'])  # Default value
    dropdown_status.grid(column=3, row=1, pady=(0, 10), padx=5, )

    # Remove Entry Button
    button_remove = ctk.CTkButton(
        mini_frame,
        text="Remove Entry",
        font=("Arial", 12, "bold"),
        fg_color="red",
        command=lambda: remove_anime_entry(anime['id_entry'], mini_window)
    )
    button_remove.grid(column=0, row=2, pady=30, padx=20, columnspan=2)

    # Save Changes Button
    button_save = ctk.CTkButton(
        mini_frame,
        text="Save Changes",
        font=("Arial", 12, "bold"),
        command=lambda: save_anime_changes(
            anime['id_entry'],
            entry_progress.get(),  # Progress from the entry box
            dropdown_score.get(),  # Get value from dropdown
            dropdown_status.get(),
            max_episode,
            mini_window
        )
    )
    button_save.grid(column=3, row=2, pady=30, padx=20)

    # Bind the entry field to validate progress on each key press
    entry_progress.bind("<KeyRelease>", lambda event: validate_progress())

def save_anime_changes(id_entry, new_progress, new_score, new_status, max_episode, mini_window):
    global filtered_entries  # We will modify this list to reflect the changes
    try:
        # Validate progress to not exceed max episode
        progress_value = int(new_progress)
        if progress_value > max_episode:
            messagebox.showerror("Error", f"Progress cannot exceed the max episode: {max_episode}")
            return

        # Update the entry in the database
        conn_users = connect_to_dbusers()
        cursor_users = conn_users.cursor()

        query_update = """
        UPDATE tblist
        SET progress = %s, score = %s, status = %s
        WHERE id_entry = %s
        """
        cursor_users.execute(query_update, (new_progress, new_score, new_status, id_entry))
        conn_users.commit()

        messagebox.showinfo("Success", "Entry updated successfully!")

        # Update the specific entry in filtered_entries
        for anime in filtered_entries:
            if anime['id_entry'] == id_entry:
                anime['progress'] = int(new_progress)
                anime['score'] = int(new_score)
                anime['status'] = new_status
                break

        # Close the mini window
        mini_window.destroy()

        # Reapply the current filter (if any)
        if current_filter:
            filter_anime_entries(current_filter)  # Apply the current filter again
        else:
            display_anime_entries(filtered_entries)  # If no filter, display the updated entries

    except pymysql.MySQLError as e:
        messagebox.showerror("Database Error", f"Error updating entry: {e}")
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid number for progress.")
    finally:
        if conn_users:
            conn_users.close()

def remove_anime_entry(id_entry, window):
    try:
        conn_users = connect_to_dbusers()
        cursor_users = conn_users.cursor()

        # Delete the entry from the database
        query_delete = "DELETE FROM tblist WHERE id_entry = %s"
        cursor_users.execute(query_delete, (id_entry,))
        conn_users.commit()

        messagebox.showinfo("Success", "Entry removed successfully!")
        window.destroy()  # Close the mini window

        # Refresh the displayed anime entries with the current filter
        fetch_anime_entries()
        if current_filter:
            filter_anime_entries(current_filter)  # Reapply the filter after removal
        else:
            display_anime_entries()  # If no filter, show all entries
    except pymysql.MySQLError as e:
        messagebox.showerror("Database Error", f"Error deleting anime entry: {e}")
    finally:
        if conn_users:
            conn_users.close()

def search_anime_entries():
    global filtered_entries

    search_query = textbox_search.get("1.0", "end").strip().lower()
    if not search_query:
        messagebox.showinfo("Search", "Please enter a search query.")
        return

    # Filter the entries based on the search query
    filtered_entries = [
        anime for anime in anime_entries if search_query in anime['Title'].lower()
    ]

    if not filtered_entries:
        messagebox.showinfo("Search", f"No anime found for '{search_query}'.")
    else:
        display_anime_entries(filtered_entries)

def create_anime_frame(parent, anime):
    """Create a frame to display a single anime entry."""
    anime_frame = ctk.CTkFrame(parent, corner_radius=10, width=600, height=50)
    anime_frame.pack(pady=5, padx=5, fill="x", expand=True)

    # Title
    label_title = ctk.CTkLabel(anime_frame, text=f"{anime['Title']}", font=("Arial", 14, "bold"))
    label_title.grid(row=0, column=1, padx=10, pady=5, sticky="w")

    # Score
    label_score = ctk.CTkLabel(anime_frame, text=f"Score: {anime['score']}")
    label_score.grid(row=1, column=1, padx=10, pady=5, sticky="w")

    # Status
    label_status = ctk.CTkLabel(anime_frame, text=f"Status: {anime['status']}")
    label_status.grid(row=2, column=1, padx=10, pady=5, sticky="w")

    # Progress (use get to avoid missing key error)
    episode = anime.get('episode', 'N/A')  # Default to 'N/A' if 'episode' is missing
    label_progress = ctk.CTkLabel(anime_frame, text=f"Progress: {anime['progress']}/{episode}")
    label_progress.grid(row=0, column=2, padx=10, pady=5, sticky="e")

    # Image
    try:
        image_url = anime['ImageURL']
        image_path = os.path.join(os.path.dirname(__file__), image_url)
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        img = Image.open(image_path)
        img = img.resize((80, 120))
        img_tk = ImageTk.PhotoImage(img)
        label_image = ctk.CTkLabel(anime_frame, image=img_tk, text="")  # Blank text since image is shown
        label_image.image = img_tk
        label_image.grid(row=0, column=0, rowspan=3, padx=10, pady=5, sticky="w")
    except Exception as e:
        print(f"Error loading image for {anime['Title']}: {e}")

    # Buttons for Progress and Edit
    button_add = ctk.CTkButton(anime_frame, text="+1", width=50, command=lambda: increment_progress(anime['id_entry']))
    button_add.grid(row=1, column=2, padx=10, pady=10, sticky="e")

    button_edit = ctk.CTkButton(anime_frame, text="Edit", width=50, command=lambda animex=anime: edit_anime_entry(animex))
    button_edit.grid(row=2, column=2, padx=10, pady=10, sticky="e")

    # Grid column configuration
    anime_frame.grid_columnconfigure(0, weight=0)  # Image column
    anime_frame.grid_columnconfigure(1, weight=1)  # Title, score, and status column
    anime_frame.grid_columnconfigure(2, weight=0)  # Buttons column

    return anime_frame

def filter_anime_entries(status_filter):
    global current_filter, filtered_entries

    current_filter = status_filter  # Update the current filter

    if status_filter == "All":
        filtered_entries = anime_entries  # Show all entries
    else:
        filtered_entries = [
            anime for anime in anime_entries if anime["status"].lower() == status_filter.lower()
        ]

    # Display the filtered list
    sort_anime_entries(current_sort_by)  # Sort the filtered entries
    display_anime_entries(filtered_entries)  # Display the filtered list

def filter_anime_by_status(status):
    """Filter anime entries based on the selected status."""
    if status == "ALL":
        filtered_entries = fetch_anime_entries()  # Fetch all entries
        # Sort alphabetically by default
        filtered_entries.sort(key=lambda anime: anime["Title"].lower())
    else:
        all_entries = fetch_anime_entries()
        # Filter by status
        filtered_entries = [anime for anime in all_entries if anime['status'].lower() == status.lower()]

    # Display the filtered/sorted list
    display_anime_entries(filtered_entries)

def display_anime_entries(entries_to_display=None):
    """Display anime entries with optional filtering."""
    # Clear previous entries
    for widget in main_frame.winfo_children():
        widget.destroy()

    # Use entries_to_display if provided, otherwise fallback to filtered_entries
    anime_entries_to_display = entries_to_display if entries_to_display is not None else filtered_entries

    if not anime_entries_to_display:
        label_empty = ctk.CTkLabel(main_frame, text="No anime entries found!", font=("Arial", 14, "bold"))
        label_empty.pack(pady=10)
        return

    for anime in anime_entries_to_display:
        create_anime_frame(main_frame, anime)

def sort_anime_entries(sort_by):
    global is_ascending, current_sort_by, filtered_entries

    current_sort_by = sort_by  # Update the current sorting field

    # Determine the sorting key and order
    key_mapping = {
        "Score": lambda anime: anime["score"],
        "Alphabet": lambda anime: anime["Title"].lower(),
        "Watched Episode": lambda anime: anime["progress"],
    }
    key_func = key_mapping.get(sort_by, lambda anime: anime["Title"].lower())

    # Sort the filtered entries
    filtered_entries.sort(key=key_func, reverse=not is_ascending)

    # Refresh the display
    display_anime_entries(filtered_entries)

def toggle_sort_order():
    global is_ascending

    # Toggle the sorting order
    is_ascending = not is_ascending

    # Sort the filtered entries
    sort_anime_entries(current_sort_by)

    # Update button text to indicate the current order
    button_ascend_descend.configure(text="^" if is_ascending else "v")

def change_sorting_criterion(sort_by):
    global current_sort_by

    # Update the current sorting criterion
    current_sort_by = sort_by

    # Sort immediately using the new criterion
    sort_anime_entries(sort_by)

def configure_scroll(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

# UI Design ======================================================================================

# Set up the main application window
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
app = ctk.CTk()
app.geometry("800x700+10+10")
app.title("Home")

# Frame 1 (Top Header)
frame1 = ctk.CTkFrame(app, fg_color="black", corner_radius=0)
frame1.pack( fill="x", side="top")
frame1.columnconfigure(0, weight=1)
frame1.columnconfigure(1, weight=1)
frame1.columnconfigure(2, weight=1)
frame1.rowconfigure(0, weight=1)
frame1.rowconfigure(1, weight=1)

# Header Content
label_title = ctk.CTkLabel(frame1, text="  AniLog  ", font=("Bahnschrift", 24, "bold"), fg_color="darkblue",
                           corner_radius=10)
label_title.grid(row=0, column=0, padx=20, pady=20, rowspan=2, sticky="w")

label_welcome = ctk.CTkLabel(frame1, text=f"Welcome! {user_name}", font=("Bahnschrift", 15, "bold"))
label_welcome.grid(row=0, column=1, rowspan=2)

button_logout = ctk.CTkButton(frame1, text="LOGOUT", font=('Arial', 12, 'bold'), width=100, command=logout)
button_logout.grid(row=0, column=2, padx=20, pady=20, sticky="e")

button_addEntry = ctk.CTkButton(frame1, text="ADD ENTRY", font=('Arial', 12, 'bold'), width=100, command=go_search)
button_addEntry.grid(row=1, column=2, padx=20, pady=20, sticky="e")

# Left Frame
left_frame = ctk.CTkFrame(app, corner_radius=10)
left_frame.pack(padx=30, pady=10, side="left")

# All button
textbox_all = ctk.CTkButton(left_frame, text="ALL", font=('Arial', 12, 'bold'), command=lambda: filter_anime_entries("All"))
textbox_all.grid(padx=10, pady=15, column=0, row=0)

# Watching button
textbox_watching = ctk.CTkButton(left_frame, text="WATCHING", font=('Arial', 12, 'bold'), command=lambda: filter_anime_entries("Watching"))
textbox_watching.grid(padx=10, pady=15, column=0, row=1)

# Completed button
textbox_completed = ctk.CTkButton(left_frame, text="COMPLETED", font=('Arial', 12, 'bold'), command=lambda: filter_anime_entries("Completed"))
textbox_completed.grid(padx=10, pady=15, column=0, row=2)

# On Hold button
textbox_onhold = ctk.CTkButton(left_frame, text="ON HOLD", font=('Arial', 12, 'bold'), command=lambda: filter_anime_entries("On Hold"))
textbox_onhold.grid(padx=10, pady=15, column=0, row=3)

# Dropped button
textbox_dropped = ctk.CTkButton(left_frame, text="DROPPED", font=('Arial', 12, 'bold'), command=lambda: filter_anime_entries("Dropped"))
textbox_dropped.grid(padx=10, pady=15, column=0, row=4)

# Plan to watch button
textbox_ptw = ctk.CTkButton(left_frame, text="PLAN TO WATCH", font=('Arial', 12, 'bold'), command=lambda: filter_anime_entries("Plan to Watch"))
textbox_ptw.grid(padx=10, pady=15, column=0, row=5)

# Outer Frame
outerFrame = ctk.CTkFrame(app, fg_color="transparent")
outerFrame.pack(expand=False, pady=10, padx=(0, 10), side="top")

# Frame 2 (Search)
frame2 = ctk.CTkFrame(outerFrame, fg_color="transparent")
frame2.pack(expand=True, pady=10, padx=(0, 0))

# Search Box
textbox_search = ctk.CTkTextbox(frame2, height=1, width=300, font=('Arial', 12,))
textbox_search.grid(row=0, column=0, padx=10)

# Search Button
textbox_search_button = ctk.CTkButton(frame2, text="SEARCH", font=('Arial', 12, 'bold'), command=search_anime_entries)
textbox_search_button.grid(row=0, column=1, padx=10)

# Frame 3 (Sort By)
frame3 = ctk.CTkFrame(outerFrame, fg_color="transparent", width=480, height=30)
frame3.pack(expand=True)

# Label Sort by
label_sortBy = ctk.CTkLabel(frame3, text="SORT BY: ", font=('Arial', 12, 'bold'))
label_sortBy.grid(row=0, column=0, padx=10)

# Variable to store the selected sort option
sort_option = ctk.StringVar(value="Alphabetical")

# Alphabetical Radio Button
radio_alphabetical = ctk.CTkRadioButton(frame3, text="Alphabetical", font=('Arial', 12, 'bold'),
                                        variable=sort_option, value="Alphabetical",
                                        command=lambda: change_sorting_criterion("Alphabet"))
radio_alphabetical.grid(row=0, column=1, padx=10)

# Watched Episode Radio Button
radio_watched_episode = ctk.CTkRadioButton(frame3, text="Watched Episode", font=('Arial', 12, 'bold'),
                                           variable=sort_option, value="Watched Episode",
                                           command=lambda: change_sorting_criterion("Watched Episode"))
radio_watched_episode.grid(row=0, column=2, padx=10)

# Score Radio Button
radio_score = ctk.CTkRadioButton(frame3, text="Score", font=('Arial', 12, 'bold'),
                                 variable=sort_option, value="Score",
                                 command=lambda: change_sorting_criterion("Score"))
radio_score.grid(row=0, column=3, padx=10)

# Ascending/Descending Button
button_ascend_descend = ctk.CTkButton(frame3, text="^", font=('Arial', 12, 'bold'), width=40,
                                      command=toggle_sort_order)
button_ascend_descend.grid(row=0, column=4, padx=10)

# Frame 4 (Scrollable Anime Entries)
scrollable_frame = ctk.CTkFrame(app)
scrollable_frame.pack(pady=10, padx=10, fill="both", expand=True)

# Add a canvas to enable scrolling
canvas = ctk.CTkCanvas(scrollable_frame, bg="#282424", highlightthickness=0)
canvas.pack(side="left", fill="both", expand=True)

# Add a scrollbar
scrollbar = ctk.CTkScrollbar(scrollable_frame, orientation="vertical", command=canvas.yview)
scrollbar.pack(side="right", fill="y")

# Configure the canvas to work with the scrollbar
canvas.configure(yscrollcommand=scrollbar.set)

# Create a frame inside the canvas
main_frame = ctk.CTkFrame(canvas,)
canvas_window = canvas.create_window((0, 0), window=main_frame, anchor="nw", width=canvas.winfo_width())

# Bind events to adjust main_frame width
main_frame.bind("<Configure>", configure_scroll)
canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

# Configure main_frame to expand
main_frame.grid_columnconfigure(0, weight=1)
main_frame.grid_rowconfigure(0, weight=1)

# After the UI setup, set the default view to "ALL"
filter_anime_by_status("ALL")

# Run the application
app.mainloop()
