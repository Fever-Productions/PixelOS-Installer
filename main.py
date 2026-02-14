import customtkinter as ctk
import subprocess
import threading
import os
import time
import requests
import shutil
import json
import concurrent.futures
import re
from tkinter import filedialog, messagebox

# --- CONFIGURATION ---
ADB_PATH = os.path.join("bin", "platform-tools", "adb")
FASTBOOT_PATH = os.path.join("bin", "platform-tools", "fastboot")
PAYLOAD_DUMPER_PATH = os.path.join("bin", "payload-dumper-go", "payload-dumper-go")
DOWNLOAD_DIR = "downloads"
GITHUB_API_URL = "https://api.github.com/repos/PixelOS-AOSP/official_devices/contents/API/devices?ref=sixteen"

# --- PARTITION GROUPS ---
# 1. PHYSICAL PARTITIONS (Flash in Bootloader)
PARTITIONS_BOOTLOADER = [
    "vbmeta", "vbmeta_system", "vbmeta_vendor", "boot", "dtbo", "vendor_boot", "recovery"
]

# 2. LOGICAL PARTITIONS (Flash in FastbootD)
PARTITIONS_FASTBOOTD = [
    "system", "system_ext", "system_b", "product", "vendor", "odm"
]

class PixelOSInstaller(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PixelOS Installer v1.2 (Dynamic Partitions)")
        self.geometry("1000x750")
        ctk.set_appearance_mode("Dark")
        
        self.device_map = {} 
        self.selected_device_data = None
        self.local_file_path = None
        self.debug_mode = False
        self.selected_device_name = ctk.StringVar(value="Loading...")
        self.is_running = False

        self.setup_ui()
        self.ensure_directories()
        self.after(500, self.refresh_devices_list)

    def ensure_directories(self):
        if not os.path.exists(DOWNLOAD_DIR):
            os.makedirs(DOWNLOAD_DIR)

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo = ctk.CTkLabel(self.sidebar, text="PixelOS\nInstaller", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo.grid(row=0, column=0, padx=20, pady=(30, 20))

        # Mode A
        self.lbl_mode1 = ctk.CTkLabel(self.sidebar, text="--- OPTION A: AUTO ---", text_color="gray")
        self.lbl_mode1.grid(row=1, column=0, pady=(10, 5))
        self.lbl_dev = ctk.CTkLabel(self.sidebar, text="Select Device:", anchor="w")
        self.lbl_dev.grid(row=2, column=0, padx=20, pady=0, sticky="w")
        self.device_dropdown = ctk.CTkOptionMenu(self.sidebar, variable=self.selected_device_name, values=[], command=self.on_device_select)
        self.device_dropdown.grid(row=3, column=0, padx=20, pady=5, sticky="ew")

        # Mode B
        self.lbl_mode2 = ctk.CTkLabel(self.sidebar, text="--- OPTION B: MANUAL ---", text_color="gray")
        self.lbl_mode2.grid(row=4, column=0, pady=(20, 5))
        self.btn_select_file = ctk.CTkButton(self.sidebar, text="Select Local File", command=self.select_local_file, fg_color="#555555", hover_color="#444444")
        self.btn_select_file.grid(row=6, column=0, padx=20, pady=5, sticky="ew")
        self.lbl_selected_file = ctk.CTkLabel(self.sidebar, text="No file selected", font=ctk.CTkFont(size=10), text_color="gray")
        self.lbl_selected_file.grid(row=7, column=0, padx=20, pady=(0, 10))

        # Info & Console
        self.info_box = ctk.CTkTextbox(self.sidebar, height=120, fg_color="#2b2b2b", text_color="gray")
        self.info_box.grid(row=8, column=0, padx=20, pady=10, sticky="ew")
        self.info_box.configure(state="disabled")
        self.console_switch = ctk.CTkSwitch(self.sidebar, text="Debug Console", command=self.toggle_debug)
        self.console_switch.grid(row=10, column=0, padx=20, pady=20, sticky="s")
        
        # Main Area
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_area.grid_rowconfigure(2, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(self.main_area, text="Ready", font=ctk.CTkFont(size=18))
        self.status_label.grid(row=0, column=0, sticky="w", pady=(0, 10))
        self.btn_install = ctk.CTkButton(self.main_area, text="START INSTALLATION", height=50, command=self.start_installation_thread, font=ctk.CTkFont(size=16, weight="bold"))
        self.btn_install.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        self.log_box = ctk.CTkTextbox(self.main_area, font=("Consolas", 12))
        self.log_box.grid(row=2, column=0, sticky="nsew")
        self.log_box.configure(state="disabled")
        self.progress = ctk.CTkProgressBar(self.main_area)
        self.progress.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        self.progress.set(0)

    # --- UI EVENTS ---
    def select_local_file(self):
        self.selected_device_name.set("Manual Mode")
        self.selected_device_data = None
        self.local_file_path = filedialog.askopenfilename(filetypes=[("ROM Files", "*.zip *.bin")])
        if self.local_file_path:
            self.lbl_selected_file.configure(text=f"Selected: {os.path.basename(self.local_file_path)}", text_color="#2CC985")
            self.status_label.configure(text="Ready to install from local file")

    def on_device_select(self, selection):
        self.local_file_path = None
        self.lbl_selected_file.configure(text="No file selected", text_color="gray")
        if selection in self.device_map:
            self.selected_device_data = self.device_map[selection]
            self.status_label.configure(text=f"Ready: {self.selected_device_data['model']}")

    # --- API ---
    def refresh_devices_list(self):
        self.log("Fetching devices...")
        threading.Thread(target=self._fetch_devices_thread, daemon=True).start()

    def _fetch_devices_thread(self):
        try:
            r = requests.get(GITHUB_API_URL)
            if r.status_code != 200: return
            
            temp_map = {}
            display_list = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = {executor.submit(requests.get, i['download_url']): i for i in r.json() if i['name'].endswith('.json')}
                for f in concurrent.futures.as_completed(futures):
                    try:
                        data = f.result().json()
                        if data.get("active"):
                            name = f"{data.get('vendor')} {data.get('model')} ({data.get('codename')})"
                            temp_map[name] = data
                            temp_map[name]['url'] = data.get('download_link')
                            display_list.append(name)
                    except: continue

            display_list.sort()
            self.device_map = temp_map
            self.after(0, lambda: self.device_dropdown.configure(values=display_list))
            self.log(f"Loaded {len(display_list)} devices.")
        except Exception as e: self.log(f"API Error: {e}")

    # --- INSTALLATION LOGIC ---
    def start_installation_thread(self):
        if not self.local_file_path and not self.selected_device_data:
            messagebox.showwarning("Error", "Select a device or file first.")
            return
        self.is_running = True
        self.btn_install.configure(state="disabled")
        threading.Thread(target=self.run_install_process, daemon=True).start()

    def run_install_process(self):
        try:
            # 1. SETUP
            zip_path = self.local_file_path
            if not zip_path:
                zip_path = os.path.join(DOWNLOAD_DIR, f"PixelOS_{self.selected_device_data['codename']}.zip")
                if not os.path.exists(zip_path):
                    self.download_file(self.selected_device_data['url'], zip_path)

            # 2. EXTRACT
            self.log("Extracting payload (Please wait)...")
            extract_dir = os.path.join(DOWNLOAD_DIR, "extracted_temp")
            if os.path.exists(extract_dir): shutil.rmtree(extract_dir)
            self.run_cmd([PAYLOAD_DUMPER_PATH, "-o", extract_dir, zip_path])

            flash_dir = None
            for root, _, files in os.walk(extract_dir):
                if "boot.img" in files:
                    flash_dir = root
                    break
            if not flash_dir: raise Exception("Extraction failed (boot.img missing).")

            # 3. BOOTLOADER PHASE
            self.log("--- PHASE 1: BOOTLOADER FLASHING ---")
            self.ensure_connection("bootloader")
            self.log("Wiping Data...")
            self.run_cmd([FASTBOOT_PATH, "-w"])

            for part in PARTITIONS_BOOTLOADER:
                self.flash_partition(part, flash_dir)

            # 4. FASTBOOTD PHASE (CRITICAL FIX)
            self.log("--- PHASE 2: SWITCHING TO FASTBOOTD ---")
            self.log("Rebooting into userspace fastboot...")
            self.run_cmd([FASTBOOT_PATH, "reboot", "fastboot"])
            
            # Wait for device to switch modes
            time.sleep(10)
            self.ensure_connection("fastbootd")

            self.log("--- PHASE 3: LOGICAL PARTITION FLASHING ---")
            # Flashing system, product, vendor...
            for part in PARTITIONS_FASTBOOTD:
                self.flash_partition(part, flash_dir)

            self.log("Rebooting to System...")
            self.run_cmd([FASTBOOT_PATH, "reboot"])
            self.status_label.configure(text="Success!", text_color="#2CC985")
            messagebox.showinfo("Success", "PixelOS Installed Successfully!")

        except Exception as e:
            self.log(f"ERROR: {e}")
            self.status_label.configure(text="Failed", text_color="#FF5555")
        finally:
            self.is_running = False
            self.btn_install.configure(state="normal")

    # --- HELPERS ---
    def flash_partition(self, part_name, flash_dir):
        img_path = os.path.join(flash_dir, f"{part_name}.img")
        if os.path.exists(img_path) and os.path.getsize(img_path) > 0:
            self.log(f"Flashing {part_name}...")
            self.run_cmd([FASTBOOT_PATH, "flash", part_name, img_path])
        else:
            self.log(f"Skipping {part_name} (Not found)")

    def ensure_connection(self, required_mode):
        self.log(f"Checking for {required_mode} connection...")
        
        for i in range(10): # Try for 10 seconds
            out = self.run_cmd_output([FASTBOOT_PATH, "devices"])
            if "fastboot" in out:
                # Optional: Check 'getvar is-userspace' to distinguish modes precisely
                # but for now, simple detection is usually enough if we just rebooted.
                return
            time.sleep(2)
            
        # Fallback: check ADB
        adb_out = self.run_cmd_output([ADB_PATH, "devices"])
        if "device" in adb_out:
            self.log("Device in ADB. Rebooting to bootloader...")
            self.run_cmd([ADB_PATH, "reboot", "bootloader"])
            time.sleep(5)
            return

        raise Exception("Device not found! Check USB.")

    def download_file(self, url, dest):
        self.log(f"Downloading ROM...")
        with requests.get(url, stream=True) as r:
            with open(dest, 'wb') as f:
                for chunk in r.iter_content(8192): f.write(chunk)

    def log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
        print(msg)

    def run_cmd(self, cmd):
        # ANSI Cleaning Logic included
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', creationflags=0x08000000)
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        for line in proc.stdout:
            clean = ansi_escape.sub('', line).strip()
            if clean and "…" not in clean: self.log(clean)
        proc.wait()
        if proc.returncode != 0: raise Exception(f"Command failed: {cmd[0]}")

    def run_cmd_output(self, cmd):
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, creationflags=0x08000000)

    def toggle_debug(self): pass 

if __name__ == "__main__":
    app = PixelOSInstaller()
    app.mainloop()