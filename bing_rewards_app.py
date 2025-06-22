import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import threading
import subprocess
import os
import sys
import signal
import sv_ttk

class BingRewardsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bing Rewards Farmer")
        self.root.geometry("700x550")
        self.root.minsize(600, 450)

        # --- Process & State Tracking ---
        self.process = None
        self.automation_running = False

        # --- UI Setup ---
        self.setup_ui()

        # --- Load Previous Settings ---
        self.load_settings()

    def setup_ui(self):
        # --- Main Layout Frames ---
        main_frame = ttk.Frame(self.root, padding=(20, 10))
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # --- Configuration Section ---
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding=15)
        config_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)

        # Driver Path
        ttk.Label(config_frame, text="Edge WebDriver").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.driver_path = tk.StringVar()
        driver_entry = ttk.Entry(config_frame, textvariable=self.driver_path)
        driver_entry.grid(row=0, column=1, sticky="ew")
        browse_btn = ttk.Button(config_frame, text="Browse", command=self.browse_driver)
        browse_btn.grid(row=0, column=2, sticky="e", padx=(10, 0))

        # Search Counts
        counts_frame = ttk.Frame(config_frame)
        counts_frame.grid(row=1, column=0, columnspan=3, sticky="w", pady=(10, 0))
        
        ttk.Label(counts_frame, text="Desktop:").pack(side=tk.LEFT)
        self.desktop_count = tk.IntVar(value=30)
        desktop_spin = ttk.Spinbox(counts_frame, from_=0, to=100, textvariable=self.desktop_count, width=5)
        desktop_spin.pack(side=tk.LEFT, padx=(5, 20))

        ttk.Label(counts_frame, text="Mobile:").pack(side=tk.LEFT)
        self.mobile_count = tk.IntVar(value=20)
        mobile_spin = ttk.Spinbox(counts_frame, from_=0, to=100, textvariable=self.mobile_count, width=5)
        mobile_spin.pack(side=tk.LEFT, padx=5)

        # Headless Mode Checkbox
        self.headless_var = tk.BooleanVar(value=True)
        headless_check = ttk.Checkbutton(counts_frame, text="Run in Background", variable=self.headless_var)
        headless_check.pack(side=tk.LEFT, padx=(20, 0))

        # --- Console Output Section ---
        console_frame = ttk.LabelFrame(main_frame, text="Console Output", padding=10)
        console_frame.grid(row=1, column=0, sticky="nsew", pady=10)
        console_frame.rowconfigure(0, weight=1)
        console_frame.columnconfigure(0, weight=1)

        self.console = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD, height=10, relief=tk.FLAT)
        self.console.grid(row=0, column=0, sticky="nsew")
        self.console.configure(font=("Consolas", 10))

        # --- Actions & Status Section ---
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=2, column=0, sticky="ew")
        action_frame.columnconfigure(1, weight=1)

        self.start_button = ttk.Button(action_frame, text="Start Farming", command=self.start_automation, style="Accent.TButton")
        self.start_button.grid(row=0, column=0, sticky="w", padx=(0, 5))

        self.stop_button = ttk.Button(action_frame, text="Stop", command=self.stop_automation, state="disabled")
        self.stop_button.grid(row=0, column=1, sticky="w")

        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(action_frame, textvariable=self.status_var, anchor="e")
        status_label.grid(row=0, column=2, sticky="e")
        action_frame.columnconfigure(2, weight=1)

    def browse_driver(self):
        filename = filedialog.askopenfilename(title="Select Edge WebDriver", filetypes=[("Executable", "*.exe")])
        if filename:
            self.driver_path.set(os.path.normpath(filename))
            self.save_settings()

    def save_settings(self):
        try:
            with open("bing_rewards_settings.txt", "w") as f:
                f.write(f"driver_path={self.driver_path.get()}\n")
                f.write(f"desktop_count={self.desktop_count.get()}\n")
                f.write(f"mobile_count={self.mobile_count.get()}\n")
                f.write(f"headless={self.headless_var.get()}\n")
        except IOError as e:
            self.console.insert(tk.END, f"Error saving settings: {e}\n")

    def load_settings(self):
        try:
            if os.path.exists("bing_rewards_settings.txt"):
                with open("bing_rewards_settings.txt", "r") as f:
                    settings = dict(line.strip().split("=", 1) for line in f if "=" in line)
                    self.driver_path.set(settings.get("driver_path", ""))
                    self.desktop_count.set(int(settings.get("desktop_count", 30)))
                    self.mobile_count.set(int(settings.get("mobile_count", 20)))
                    self.headless_var.set(settings.get("headless", "True") == "True")
        except (IOError, ValueError) as e:
            self.console.insert(tk.END, f"Error loading settings: {e}\n")

    def stop_automation(self):
        if self.process and self.automation_running:
            self.console.insert(tk.END, "\n⚠️ Stopping automation...\n")
            self.automation_running = False
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.process.pid)], capture_output=True)
            else:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.status_var.set("Stopped by user")
            self.stop_button.configure(state="disabled")
            self.start_button.configure(state="normal")

    def start_automation(self):
        if not self.driver_path.get() or not os.path.exists(self.driver_path.get()):
            self.status_var.set("Error: WebDriver path is invalid.")
            return

        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_var.set("Running...")
        self.automation_running = True
        self.save_settings()
        self.console.delete(1.0, tk.END)
        os.makedirs("logs", exist_ok=True)
        threading.Thread(target=self.run_automation_process, daemon=True).start()

    def run_automation_process(self):
        try:
            script_path = os.path.join(os.path.dirname(__file__), "bing_rewards_automation.py")
            cmd = [
                sys.executable, script_path,
                "--driver-path", self.driver_path.get(),
                "--desktop", str(self.desktop_count.get()),
                "--mobile", str(self.mobile_count.get()),
                "--log-dir", "logs"
            ]
            
            if self.headless_var.get():
                cmd.append("--headless")

            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, bufsize=1, creationflags=creation_flags
            )

            for line in self.process.stdout:
                if not self.automation_running: break
                self.console.insert(tk.END, line)
                self.console.see(tk.END)
            
            self.process.wait()

            if self.automation_running: # If not stopped manually
                if self.process.returncode == 0:
                    self.status_var.set("✅ Completed successfully!")
                else:
                    self.status_var.set(f"❌ Failed (exit code {self.process.returncode})")
        except Exception as e:
            self.status_var.set(f"❌ Error: {e}")
        finally:
            self.automation_running = False
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    sv_ttk.set_theme("light")
    app = BingRewardsApp(root)
    root.mainloop()