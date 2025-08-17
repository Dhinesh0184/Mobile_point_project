from tkinter import *
from tkinter import ttk, messagebox
from datetime import datetime
import sqlite3
import os
import csv
from tkinter import filedialog

# === COLORS AND FONTS ===
BG_COLOR = "#1e272e"
FRAME_BG = "#2f3640"
BTN_COLOR = "#00a8ff"
BTN_HOVER = "#0097e6"
TEXT_COLOR = "#dcdde1"
ENTRY_BG = "#3d3d3d"
ENTRY_FG = "white"
FONT = ("Segoe UI", 14)
FONT_BOLD = ("Segoe UI", 16, "bold")

# === DATABASE SETUP ===
con = sqlite3.connect("mobile_point.db")
cur = con.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS mobile_records (
        token INTEGER PRIMARY KEY,
        roll_number TEXT,
        in_time TEXT,
        out_time TEXT
    )
""")
con.commit()

# === ROOT WINDOW ===
root = Tk()
root.title("MOBILE POINT")
root.geometry("1280x720")
root.config(bg=BG_COLOR)
root.state("zoomed")

# === UTILITY FUNCTIONS ===
def on_enter(e):
    e.widget['background'] = BTN_HOVER

def on_leave(e):
    e.widget['background'] = BTN_COLOR

def format_duration(seconds):
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    return f"{int(hours):02d}:{int(mins):02d}:{int(secs):02d}"

def update_dashboard():
    cur.execute("SELECT COUNT(*) FROM mobile_records")
    total = cur.fetchone()[0]
    total_tokens_val.config(text=str(total))

    cur.execute("SELECT COUNT(*) FROM mobile_records WHERE out_time IS NULL")
    inside = cur.fetchone()[0]
    mobiles_inside_val.config(text=str(inside))

    cur.execute("SELECT in_time, out_time FROM mobile_records WHERE out_time IS NOT NULL")
    durations = [(datetime.fromisoformat(o) - datetime.fromisoformat(i)).total_seconds()
                 for i, o in cur.fetchall() if i and o]
    avg = format_duration(sum(durations)/len(durations)) if durations else "00:00:00"
    avg_duration_val.config(text=avg)

def clear_entry():
    txtRoll.delete(0, END)

def refresh_treeview():
    for item in tv.get_children():
        tv.delete(item)
    cur.execute("SELECT * FROM mobile_records")
    for token, roll, i_time, o_time in cur.fetchall():
        in_time_str = i_time
        out_time_str = o_time if o_time else "N/A"
        duration_str = format_duration((datetime.fromisoformat(o_time) - datetime.fromisoformat(i_time)).total_seconds()) if o_time else "-"
        tv.insert('', 'end', values=(token, roll, in_time_str, out_time_str, duration_str))

def allocate_slot():
    roll = txtRoll.get().strip()
    if not roll:
        messagebox.showwarning("Input Error", "Please enter roll number.")
        return

    cur.execute("SELECT * FROM mobile_records WHERE roll_number=? AND out_time IS NULL", (roll,))
    if cur.fetchone():
        messagebox.showinfo("Already Allocated", f"Mobile already allocated to {roll}.")
        return

    now = datetime.now().isoformat()
    cur.execute("INSERT INTO mobile_records (roll_number, in_time) VALUES (?, ?)", (roll, now))
    con.commit()
    refresh_treeview()
    update_dashboard()
    clear_entry()

def deallocate_slot():
    roll = txtRoll.get().strip()
    if not roll:
        messagebox.showwarning("Input Error", "Please enter roll number.")
        return

    cur.execute("SELECT token FROM mobile_records WHERE roll_number=? AND out_time IS NULL", (roll,))
    row = cur.fetchone()
    if row:
        now = datetime.now().isoformat()
        cur.execute("UPDATE mobile_records SET out_time=? WHERE token=?", (now, row[0]))
        con.commit()
        refresh_treeview()
        update_dashboard()
        clear_entry()
        messagebox.showinfo("Deallocated", f"Mobile returned for roll {roll}.")
    else:
        messagebox.showinfo("Not Found", f"No active allocation found for roll {roll}.")

# === DASHBOARD FRAME ===
dashboard_frame = Frame(root, bg=FRAME_BG, pady=15)
dashboard_frame.pack(fill=X, padx=20, pady=15)

Label(dashboard_frame, text="Dashboard", font=FONT_BOLD, bg=FRAME_BG, fg=TEXT_COLOR).grid(row=0, column=0, padx=10, sticky=W)

Label(dashboard_frame, text="Total Tokens Issued:", font=FONT, bg=FRAME_BG, fg=TEXT_COLOR).grid(row=1, column=0, padx=10, pady=5, sticky=W)
total_tokens_val = Label(dashboard_frame, text="0", font=FONT_BOLD, bg=FRAME_BG, fg="#00ff96")
total_tokens_val.grid(row=1, column=1, padx=10, sticky=W)

Label(dashboard_frame, text="Mobiles Inside:", font=FONT, bg=FRAME_BG, fg=TEXT_COLOR).grid(row=1, column=2, padx=10, pady=5, sticky=W)
mobiles_inside_val = Label(dashboard_frame, text="0", font=FONT_BOLD, bg=FRAME_BG, fg="#ffd32a")
mobiles_inside_val.grid(row=1, column=3, padx=10, sticky=W)

Label(dashboard_frame, text="Avg Duration:", font=FONT, bg=FRAME_BG, fg=TEXT_COLOR).grid(row=1, column=4, padx=10, pady=5, sticky=W)
avg_duration_val = Label(dashboard_frame, text="00:00:00", font=FONT_BOLD, bg=FRAME_BG, fg="#ff5252")
avg_duration_val.grid(row=1, column=5, padx=10, sticky=W)

def export_to_csv():
    global data  # <-- Add this line!
    if not data:
        messagebox.showinfo("No Data", "No records to export.")
        return
    file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                             filetypes=[("CSV Files", "*.csv")],
                                             title="Save As")
    if file_path:
        try:
            with open(file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Token Number", "Roll Number", "In-Time", "Out-Time", "Duration"])
                for record in data:
                    in_time = record['in_time'].strftime("%Y-%m-%d %H:%M:%S")
                    out_time = record['out_time'].strftime("%Y-%m-%d %H:%M:%S") if record['out_time'] else "N/A"
                    duration = format_duration((record['out_time'] - record['in_time']).total_seconds()) if record['out_time'] else "-"
                    writer.writerow([record['token'], record['roll_number'], in_time, out_time, duration])
            messagebox.showinfo("Success", f"Data exported successfully to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")

# === ENTRIES FRAME ===
entries_frame = Frame(root, bg=FRAME_BG, bd=0, relief=RIDGE)
entries_frame.pack(side=TOP, fill=X, padx=20, pady=10)

Label(entries_frame, text="Roll Number", font=FONT, bg=FRAME_BG, fg=TEXT_COLOR).grid(row=0, column=0, padx=10, pady=10, sticky=W)
txtRoll = Entry(entries_frame, font=FONT, width=30, bg=ENTRY_BG, fg=ENTRY_FG, relief=FLAT, insertbackground=ENTRY_FG)
txtRoll.grid(row=0, column=1, padx=10, pady=10, sticky=W)

btn_frame = Frame(entries_frame, bg=FRAME_BG)
btn_frame.grid(row=1, column=0, columnspan=6, pady=10, sticky=W)

btnAdd = Button(btn_frame, text="Allocate Slot", width=15, font=FONT_BOLD, fg="white", bg=BTN_COLOR, bd=0, activebackground=BTN_HOVER, cursor="hand2", command=allocate_slot)
btnAdd.grid(row=0, column=0, padx=10)
btnAdd.bind("<Enter>", on_enter)
btnAdd.bind("<Leave>", on_leave)

btnDelete = Button(btn_frame, text="Deallocate Slot", width=15, font=FONT_BOLD, fg="white", bg="#e84118", bd=0, activebackground="#c23616", cursor="hand2", command=deallocate_slot)
btnDelete.grid(row=0, column=1, padx=10)
btnDelete.bind("<Enter>", lambda e: e.widget.config(bg="#c23616"))
btnDelete.bind("<Leave>", lambda e: e.widget.config(bg="#e84118"))

btnClear = Button(btn_frame, text="Clear Entry", width=15, font=FONT_BOLD, fg="white", bg="#718093", bd=0, activebackground="#57606f", cursor="hand2", command=clear_entry)
btnClear.grid(row=0, column=2, padx=10)
btnClear.bind("<Enter>", lambda e: e.widget.config(bg="#57606f"))
btnClear.bind("<Leave>", lambda e: e.widget.config(bg="#718093"))
btnExport = Button(btn_frame, text="Export to CSV", width=15, font=FONT_BOLD,
                   fg="white", bg="#10ac84", bd=0, activebackground="#079992",
                   cursor="hand2", command=export_to_csv)
btnExport.grid(row=0, column=3, padx=10)
btnExport.bind("<Enter>", lambda e: e.widget.config(bg="#079992"))
btnExport.bind("<Leave>", lambda e: e.widget.config(bg="#10ac84"))


# === TREEVIEW FRAME ===
tree_frame = Frame(root, bg=BG_COLOR)
tree_frame.pack(fill=BOTH, expand=TRUE, padx=20, pady=10)

style = ttk.Style()
style.theme_use('clam')
style.configure("Treeview",
                background="#485460",
                foreground=TEXT_COLOR,
                rowheight=35,
                fieldbackground="#485460",
                font=FONT)
style.configure("Treeview.Heading", font=(FONT[0], 16, "bold"), foreground=BTN_COLOR)
style.map('Treeview', background=[('selected', BTN_COLOR)])

tv = ttk.Treeview(tree_frame, columns=(1, 2, 3, 4, 5), show='headings', selectmode='browse')
tv.pack(fill=BOTH, expand=TRUE)

tv.heading(1, text="Token Number")
tv.column(1, width=150, anchor=CENTER)

tv.heading(2, text="Roll Number")
tv.column(2, width=250, anchor=CENTER)

tv.heading(3, text="In-Time")
tv.column(3, width=250, anchor=CENTER)

tv.heading(4, text="Out-Time")
tv.column(4, width=250, anchor=CENTER)

tv.heading(5, text="Duration (HH:MM:SS)")
tv.column(5, width=200, anchor=CENTER)

scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=tv.yview)
tv.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side=RIGHT, fill=Y)

refresh_treeview()
update_dashboard()
root.mainloop()
