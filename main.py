import hashlib
import os
import json
import time
import datetime
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog

# ==============================
# CONFIGURATION
# ==============================
SYSTEM_PASSWORD = "admin123"
DATABASE_FILE = "hash_database.json"
LOG_FILE = "log.txt"

IGNORE_FILES = ["log.txt", "hash_database.json", "main.py"]

MONITOR_FOLDERS = []
change_counter = 0
monitoring = False
app = None


# ==============================
# HASH FUNCTION
# ==============================
def calculate_hash(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as file:
        while chunk := file.read(4096):
            sha256.update(chunk)
    return sha256.hexdigest()


# ==============================
# SAFE GUI UPDATE
# ==============================
def update_output(message):
    output_box.insert(tk.END, message + "\n")
    output_box.see(tk.END)


def update_counter():
    counter_label.config(text=f"Changes Detected: {change_counter}")


def log_event(message):
    timestamp = datetime.datetime.now()
    formatted = f"[{timestamp}] {message}"

    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(formatted + "\n")

    if app:
        app.after(0, lambda: update_output(formatted))
        app.after(0, update_counter)


# ==============================
# CHECK IF FILE SHOULD BE IGNORED
# ==============================
def should_ignore(file_path):
    filename = os.path.basename(file_path)
    return filename in IGNORE_FILES


# ==============================
# FOLDER SELECTION
# ==============================
def select_folder():
    folder = filedialog.askdirectory()
    if folder:
        MONITOR_FOLDERS.clear()
        MONITOR_FOLDERS.append(folder)
        folder_label.config(text=f"Monitoring Folder: {folder}")
        log_event(f"Folder selected: {folder}")


# ==============================
# INITIAL SCAN
# ==============================
def initial_scan():
    if not MONITOR_FOLDERS:
        log_event("Please select a folder first.")
        return

    data = {}

    for folder in MONITOR_FOLDERS:
        for root, dirs, files in os.walk(folder):
            for file in files:
                path = os.path.join(root, file)

                if should_ignore(path):
                    continue

                try:
                    data[path] = calculate_hash(path)
                except:
                    continue

    with open(DATABASE_FILE, "w", encoding="utf-8") as db:
        json.dump(data, db, indent=4)

    log_event("Initial scan completed successfully.")


# ==============================
# CHECK CHANGES
# ==============================
def check_changes():
    global change_counter

    if not os.path.exists(DATABASE_FILE):
        log_event("No database found. Run initial scan first.")
        return

    with open(DATABASE_FILE, "r", encoding="utf-8") as db:
        old_data = json.load(db)

    new_data = {}

    for folder in MONITOR_FOLDERS:
        for root, dirs, files in os.walk(folder):
            for file in files:
                path = os.path.join(root, file)

                if should_ignore(path):
                    continue

                try:
                    new_hash = calculate_hash(path)
                    new_data[path] = new_hash
                except:
                    continue

                if path not in old_data:
                    log_event(f"New file detected: {path}")
                    change_counter += 1

                elif old_data[path] != new_hash:
                    log_event(f"File modified: {path}")
                    change_counter += 1

    for path in old_data:
        if path not in new_data:
            log_event(f"File deleted: {path}")
            change_counter += 1

    with open(DATABASE_FILE, "w", encoding="utf-8") as db:
        json.dump(new_data, db, indent=4)


# ==============================
# MONITORING LOOP
# ==============================
def start_monitoring():
    global monitoring

    if not MONITOR_FOLDERS:
        log_event("Please select a folder first.")
        return

    monitoring = True
    status_label.config(text="STATUS: MONITORING", fg="#00ff88")
    log_event("Monitoring started.")

    while monitoring:
        check_changes()
        time.sleep(5)


def stop_monitoring():
    global monitoring
    monitoring = False
    status_label.config(text="STATUS: STOPPED", fg="#ff4444")
    log_event("Monitoring stopped.")


# ==============================
# LOGIN SYSTEM
# ==============================
def check_login():
    if password_entry.get() == SYSTEM_PASSWORD:
        login_window.destroy()
        open_dashboard()
    else:
        messagebox.showerror("Access Denied", "Incorrect Password")


# ==============================
# DASHBOARD
# ==============================
def open_dashboard():
    global output_box, status_label, counter_label, folder_label, app

    app = tk.Tk()
    app.title("Enterprise Security Monitor")
    app.geometry("1000x650")
    app.configure(bg="#1e1e2f")

    tk.Label(
        app,
        text="ENTERPRISE FILE INTEGRITY MONITOR",
        bg="#1e1e2f",
        fg="#00ffcc",
        font=("Helvetica", 20, "bold")
    ).pack(pady=15)

    status_label = tk.Label(
        app,
        text="STATUS: STOPPED",
        bg="#1e1e2f",
        fg="#ff4444",
        font=("Helvetica", 12, "bold")
    )
    status_label.pack()

    counter_label = tk.Label(
        app,
        text="Changes Detected: 0",
        bg="#1e1e2f",
        fg="#ffaa00",
        font=("Helvetica", 12, "bold")
    )
    counter_label.pack()

    folder_label = tk.Label(
        app,
        text="Monitoring Folder: None Selected",
        bg="#1e1e2f",
        fg="#cccccc",
        font=("Helvetica", 10)
    )
    folder_label.pack(pady=5)

    button_frame = tk.Frame(app, bg="#1e1e2f")
    button_frame.pack(pady=20)

    def styled_button(text, command):
        return tk.Button(
            button_frame,
            text=text,
            command=command,
            bg="#2b2b40",
            fg="#ffffff",
            activebackground="#00ffcc",
            activeforeground="#000000",
            width=18,
            height=2,
            bd=0,
            font=("Helvetica", 10, "bold")
        )

    styled_button("Select Folder", select_folder).grid(row=0, column=0, padx=10)
    styled_button("Initial Scan", initial_scan).grid(row=0, column=1, padx=10)
    styled_button(
        "Start Monitoring",
        lambda: threading.Thread(target=start_monitoring, daemon=True).start()
    ).grid(row=0, column=2, padx=10)
    styled_button("Stop Monitoring", stop_monitoring).grid(row=0, column=3, padx=10)

    tk.Label(
        app,
        text="ACTIVITY LOG",
        bg="#1e1e2f",
        fg="#00ffcc",
        font=("Helvetica", 12, "bold")
    ).pack(pady=10)

    output_box = scrolledtext.ScrolledText(
        app,
        width=120,
        height=20,
        bg="#111122",
        fg="#00ff88",
        insertbackground="white",
        font=("Consolas", 10)
    )
    output_box.pack(pady=10)

    app.mainloop()


# ==============================
# LOGIN WINDOW
# ==============================
login_window = tk.Tk()
login_window.title("Secure Login")
login_window.geometry("350x200")
login_window.configure(bg="#1e1e2f")

tk.Label(
    login_window,
    text="SECURE SYSTEM LOGIN",
    bg="#1e1e2f",
    fg="#00ffcc",
    font=("Helvetica", 14, "bold")
).pack(pady=20)

password_entry = tk.Entry(login_window, show="*", width=25)
password_entry.pack(pady=10)

tk.Button(
    login_window,
    text="LOGIN",
    command=check_login,
    bg="#2b2b40",
    fg="white",
    width=15,
    height=1,
    bd=0,
    font=("Helvetica", 10, "bold")
).pack(pady=10)

login_window.mainloop()
