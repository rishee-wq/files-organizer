import sys
import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from threading import Thread
import time

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller bundle."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class RishFlowApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RishFlow")
        self.root.geometry("700x600")
        self.root.configure(bg="#0A1833")
        self.move_history = []

        # Load Logo at side (top only)
        try:
            logo_img = Image.open(resource_path("logo.png")).resize((50, 50))
            self.logo = ImageTk.PhotoImage(logo_img)
        except:
            self.logo = None

        # Header with Logo + Name + Quote
        header = tk.Frame(root, bg="#0A1833")
        header.pack(pady=(10, 0), fill="x", padx=20)

        if self.logo:
            logo_label = tk.Label(header, image=self.logo, bg="#0A1833")
            logo_label.pack(side="left", padx=(0, 15))
        
        text_frame = tk.Frame(header, bg="#0A1833")
        text_frame.pack(side="left")
        tk.Label(text_frame, text="RishFlow", font=("Montserrat", 26, "bold"), fg="#40E0D0", bg="#0A1833").pack()
        tk.Label(text_frame, text="Smartly Organised. Simply Rishified.", font=("Montserrat", 11, "italic"), fg="#40E0D0", bg="#0A1833").pack()

        # Folder selection
        sel_frame = tk.Frame(root, bg="#0A1833")
        sel_frame.pack(pady=15, fill="x")

        def create_browse_row(row, label_text, command):
            lbl = tk.Label(sel_frame, text=label_text, fg="#fff", bg="#0A1833", font=("Segoe UI", 10))
            lbl.grid(row=row, column=0, sticky="e", padx=5, pady=5)
            entry = tk.Entry(sel_frame, width=40, font=("Segoe UI", 10))
            entry.grid(row=row, column=1, padx=5, pady=5)
            btn = self.oval_button(sel_frame, "Browse", command)
            btn.grid(row=row, column=2, padx=5, pady=5)
            return entry

        self.src_entry = create_browse_row(0, "Source Folder:", self.browse_src)
        self.dst_entry = create_browse_row(1, "Destination Folder:", self.browse_dst)

        # Canvas for circular water fill (just percent; no logo/fish in center)
        self.canvas_size = 180
        self.canvas = tk.Canvas(root, width=self.canvas_size, height=self.canvas_size, bg="#0A1833", highlightthickness=0)
        self.canvas.pack(pady=10)
        self.circle_bg = self.canvas.create_oval(10, 10, self.canvas_size-10, self.canvas_size-10, outline="#40E0D0", width=4)
        self.water_arc = self.canvas.create_arc(10, 10, self.canvas_size-10, self.canvas_size-10, start=90, extent=0, fill="#40E0D0", outline="")
        self.percent_text = self.canvas.create_text(self.canvas_size/2, self.canvas_size/2, text="0%", fill="white", font=("Segoe UI", 20, "bold"))
        # Click circle or percent to start
        self.canvas.tag_bind(self.circle_bg, "<Button-1>", self.start_organization)
        self.canvas.tag_bind(self.water_arc, "<Button-1>", self.start_organization)
        self.canvas.tag_bind(self.percent_text, "<Button-1>", self.start_organization)

        # Undo button
        btn_frame = tk.Frame(root, bg="#0A1833")
        btn_frame.pack(pady=10)
        self.undo_btn = self.oval_button(btn_frame, "Undo Last Move", self.undo_last_move, bg="#FAD648", fg="#144c63")
        self.undo_btn.pack(side="left", padx=20)

        # Activity Log
        log_frame = ttk.LabelFrame(root, text="Activity Log", padding=8)
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.log_text = tk.Text(log_frame, height=8, width=70, bg="#192642", fg="white", font=("Consolas", 10))
        self.log_text.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scroll.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scroll.set)

        # For animation
        self.organizing = False
        self.progress_percent = 0

    def oval_button(self, master, text, command, bg="#37e8d7", fg="#144c63"):
        btn = tk.Button(master, text=text, command=command, font=("Segoe UI", 11, "bold"),
                        bg=bg, fg=fg, relief="flat", bd=0,
                        padx=15, pady=8, cursor="hand2")
        return btn

    def browse_src(self):
        folder = filedialog.askdirectory()
        if folder:
            self.src_entry.delete(0, tk.END)
            self.src_entry.insert(0, folder)

    def browse_dst(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dst_entry.delete(0, tk.END)
            self.dst_entry.insert(0, folder)

    def start_organization(self, event=None):
        src = self.src_entry.get()
        dst = self.dst_entry.get()
        if not src or not dst:
            messagebox.showerror("Error", "Select both folders")
            return
        if self.organizing:
            return
        self.organizing = True
        self.progress_percent = 0
        self.animate_progress()
        Thread(target=self.organize_files, args=(src, dst)).start()

    def undo_last_move(self):
        if not self.move_history:
            self.log("No move to undo.")
            return
        last_move = self.move_history.pop()
        shutil.move(last_move[1], last_move[0])
        self.log(f"Undid: {os.path.basename(last_move[1])}")

    def animate_progress(self):
        if not self.organizing:
            return
        self.update_water_fill(self.progress_percent)
        self.canvas.itemconfig(self.percent_text, text=f"{int(self.progress_percent)}%")
        self.root.after(100, self.animate_progress)

    def update_water_fill(self, percent):
        extent = percent * 3.6  # percent to degrees
        self.canvas.itemconfig(self.water_arc, extent=-extent)

    def organize_files(self, src, dst):
        files = [f for f in os.listdir(src) if os.path.isfile(os.path.join(src, f))]
        total = len(files)
        if total == 0:
            self.log("No files found.")
            self.organizing = False
            return
        for i, filename in enumerate(files, 1):
            if not self.organizing:
                break
            ext = os.path.splitext(filename)[1].upper()
            folder_name = ext[1:] + "_Files"
            dest_folder = os.path.join(dst, folder_name)
            os.makedirs(dest_folder, exist_ok=True)
            src_path = os.path.join(src, filename)
            dest_path = os.path.join(dest_folder, filename)
            shutil.move(src_path, dest_path)
            self.move_history.append((src_path, dest_path))
            self.progress_percent = int(i / total * 100)
            self.log(f"Moved {filename} to {folder_name}")
            self.root.update_idletasks()
            time.sleep(0.2)
        self.log("Organization completed.")
        self.organizing = False

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    root.iconphoto(False, tk.PhotoImage(file=resource_path('logo.png')))
    app = RishFlowApp(root)
    root.mainloop()
