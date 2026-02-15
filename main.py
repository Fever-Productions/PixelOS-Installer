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
import webbrowser
import google.generativeai as genai
from tkinter import filedialog, messagebox

# --- CONFIGURATION ---
ADB_PATH = os.path.join("bin", "platform-tools", "adb")
FASTBOOT_PATH = os.path.join("bin", "platform-tools", "fastboot")
PAYLOAD_DUMPER_PATH = os.path.join("bin", "payload-dumper-go", "payload-dumper-go")
DOWNLOAD_DIR = "downloads"

# APIs
PIXELOS_API_URL = "https://api.github.com/repos/PixelOS-AOSP/official_devices/contents/API/devices?ref=sixteen"
DEVICE_DB_URL = "https://raw.githubusercontent.com/PixelExperience/official_devices/master/devices.json"

# Partitions
PARTITIONS_BOOTLOADER = ["vbmeta", "vbmeta_system", "vbmeta_vendor", "boot", "dtbo", "vendor_boot", "recovery"]
PARTITIONS_FASTBOOTD = ["system", "system_ext", "system_b", "product", "vendor", "odm"]

class PixelOSInstaller(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PixelOS Installer & ROM Manager")
        self.geometry("1100x750")
        ctk.set_appearance_mode("Dark")
        
        self.pixelos_devices = {}
        self.universal_devices = {}
        self.manual_file = None
        self.selected_device_data = None
        
        self.setup_ui()
        self.ensure_directories()
        self.after(500, self.load_databases)

    def ensure_directories(self):
        if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo = ctk.CTkLabel(self.sidebar, text="PixelOS\nInstaller", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo.grid(row=0, column=0, padx=20, pady=(30, 20))

        self.btn_home = self.create_sidebar_btn("Official Installer", self.show_home, 1)
        self.btn_search = self.create_sidebar_btn("Universal Search", self.show_search, 2)
        self.btn_ai = self.create_sidebar_btn("Gemini AI Hunter", self.show_ai, 3)
        self.btn_manual = self.create_sidebar_btn("Manual Flasher", self.show_manual, 4)
        
        self.console_switch = ctk.CTkSwitch(self.sidebar, text="Debug Console")
        self.console_switch.grid(row=8, column=0, padx=20, pady=20, sticky="s")

        # --- MAIN CONTENT ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.setup_home_frame()
        self.setup_search_frame()
        self.setup_ai_frame()
        self.setup_manual_frame()

        self.show_home()

    def create_sidebar_btn(self, text, command, row):
        btn = ctk.CTkButton(self.sidebar, text=text, command=command, 
                            fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                            anchor="w", height=40, font=ctk.CTkFont(size=14))
        btn.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        return btn

    # --- FRAME SETUP ---
    def setup_home_frame(self):
        self.frame_home = ctk.CTkFrame(self.main_container, fg_color="transparent")
        ctk.CTkLabel(self.frame_home, text="Official PixelOS Installer", font=("Arial", 24, "bold")).pack(pady=(10, 20), anchor="w")
        
        self.pixelos_dropdown = ctk.CTkOptionMenu(self.frame_home, values=["Loading..."], width=300)
        self.pixelos_dropdown.pack(pady=10, anchor="w")
        
        ctk.CTkButton(self.frame_home, text="INSTALL PIXELOS", height=45, width=200, 
                      command=self.start_pixelos_install, fg_color="#3B8ED0").pack(pady=20, anchor="w")
        
        self.log_box = ctk.CTkTextbox(self.frame_home, height=250)
        self.log_box.pack(fill="both", expand=True, pady=10)
        self.log_box.configure(state="disabled")

    def setup_search_frame(self):
        self.frame_search = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.frame_search.grid_columnconfigure(0, weight=1)
        self.frame_search.grid_rowconfigure(2, weight=1)
        
        ctk.CTkLabel(self.frame_search, text="Universal ROM Search", font=("Arial", 24, "bold")).grid(row=0, column=0, sticky="w", pady=10)
        
        self.search_entry = ctk.CTkEntry(self.frame_search, placeholder_text="Device Name (e.g. Redmi Note 10)")
        self.search_entry.grid(row=1, column=0, sticky="ew", pady=10)
        self.search_entry.bind("<KeyRelease>", self.filter_devices)

        split = ctk.CTkFrame(self.frame_search, fg_color="transparent")
        split.grid(row=2, column=0, sticky="nsew")
        split.grid_columnconfigure(0, weight=1)
        split.grid_columnconfigure(1, weight=2)
        split.grid_rowconfigure(0, weight=1)

        self.device_listbox = ctk.CTkScrollableFrame(split, label_text="Device Database")
        self.device_listbox.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.results_scroll = ctk.CTkScrollableFrame(split, label_text="Results")
        self.results_scroll.grid(row=0, column=1, sticky="nsew")

    def setup_ai_frame(self):
        self.frame_ai = ctk.CTkFrame(self.main_container, fg_color="transparent")
        
        ctk.CTkLabel(self.frame_ai, text="Gemini AI ROM Hunter", font=("Arial", 24, "bold")).pack(pady=10, anchor="w")
        
        # API Key Row
        key_frame = ctk.CTkFrame(self.frame_ai, fg_color="transparent")
        key_frame.pack(fill="x", pady=5)
        
        self.api_key_entry = ctk.CTkEntry(key_frame, placeholder_text="Paste Gemini API Key Here", width=400)
        self.api_key_entry.pack(side="left", padx=(0, 10))
        
        # New Fetch Button
        ctk.CTkButton(key_frame, text="Fetch Models", width=100, command=self.fetch_gemini_models, fg_color="#E040FB").pack(side="left")

        # Model Selector Row
        model_frame = ctk.CTkFrame(self.frame_ai, fg_color="transparent")
        model_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(model_frame, text="Select Model:").pack(side="left", padx=(0, 10))
        self.model_dropdown = ctk.CTkOptionMenu(model_frame, values=["gemini-1.5-flash (Default)"], width=250)
        self.model_dropdown.pack(side="left")

        # Search Row
        self.ai_search_entry = ctk.CTkEntry(self.frame_ai, placeholder_text="Device Name (e.g. Samsung S23 Ultra)", width=400)
        self.ai_search_entry.pack(pady=10, anchor="w")
        
        ctk.CTkButton(self.frame_ai, text="Ask Gemini", command=self.ask_gemini, fg_color="#8E24AA").pack(pady=10, anchor="w")
        
        self.lbl_ai_status = ctk.CTkLabel(self.frame_ai, text="Enter Key -> Fetch Models -> Search", font=("Arial", 14))
        self.lbl_ai_status.pack(pady=10, anchor="w")
        
        self.ai_results_frame = ctk.CTkScrollableFrame(self.frame_ai)
        self.ai_results_frame.pack(fill="both", expand=True, pady=10)

    def setup_manual_frame(self):
        self.frame_manual = ctk.CTkFrame(self.main_container, fg_color="transparent")
        ctk.CTkLabel(self.frame_manual, text="Manual Flasher", font=("Arial", 24, "bold")).pack(pady=10, anchor="w")
        
        ctk.CTkButton(self.frame_manual, text="Select File", command=self.select_manual_file, height=40).pack(pady=40, anchor="w")
        self.lbl_manual = ctk.CTkLabel(self.frame_manual, text="No file selected", font=("Arial", 16))
        self.lbl_manual.pack(pady=10, anchor="w")
        
        self.btn_manual_flash = ctk.CTkButton(self.frame_manual, text="FLASH NOW", command=self.start_manual_flash, 
                                              state="disabled", fg_color="green", height=50, width=200)
        self.btn_manual_flash.pack(pady=20, anchor="w")

    # --- NAV ---
    def switch_frame(self, frame, active_btn):
        for f in [self.frame_home, self.frame_search, self.frame_ai, self.frame_manual]: f.pack_forget()
        for b in [self.btn_home, self.btn_search, self.btn_ai, self.btn_manual]: b.configure(fg_color="transparent")
        frame.pack(fill="both", expand=True)
        active_btn.configure(fg_color=("gray75", "gray25"))

    def show_home(self): self.switch_frame(self.frame_home, self.btn_home)
    def show_search(self): self.switch_frame(self.frame_search, self.btn_search)
    def show_ai(self): self.switch_frame(self.frame_ai, self.btn_ai)
    def show_manual(self): self.switch_frame(self.frame_manual, self.btn_manual)

    # --- AI LOGIC (UPDATED) ---
    def fetch_gemini_models(self):
        key = self.api_key_entry.get().strip()
        if not key:
            messagebox.showerror("Error", "Enter API Key first.")
            return

        self.lbl_ai_status.configure(text="Fetching available Gemini models...")
        threading.Thread(target=self._fetch_models_thread, args=(key,), daemon=True).start()

    def _fetch_models_thread(self, key):
        try:
            genai.configure(api_key=key)
            models = []
            # List models and filter for those that support generation
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    models.append(m.name.replace("models/", ""))
            
            # Prioritize flash/pro models visually
            models.sort(reverse=True)
            
            self.after(0, lambda: self.update_model_dropdown(models))
        except Exception as e:
            self.after(0, lambda: self.lbl_ai_status.configure(text=f"Model Error: {e}"))

    def update_model_dropdown(self, models):
        if models:
            self.model_dropdown.configure(values=models)
            self.model_dropdown.set(models[0])
            self.lbl_ai_status.configure(text=f"Loaded {len(models)} models. Ready to search.")
        else:
            self.lbl_ai_status.configure(text="No compatible models found.")

    def ask_gemini(self):
        key = self.api_key_entry.get().strip()
        device = self.ai_search_entry.get().strip()
        model_name = self.model_dropdown.get()
        
        if "Default" in model_name: model_name = "gemini-1.5-flash" # Fallback
        
        if not key or not device: return
        self.lbl_ai_status.configure(text=f"Using {model_name} to find ROMs for {device}...")
        
        threading.Thread(target=self._gemini_thread, args=(key, device, model_name), daemon=True).start()

    def _gemini_thread(self, key, device, model_name):
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel(model_name)
            
            prompt = f"""
            Identify the codename for Android device: "{device}".
            Then list 4 popular Custom ROMs for it.
            Return ONLY a valid JSON array.
            Format: [{{"rom": "LineageOS", "url": "https://...", "official": true}}]
            If URL unknown, use google search URL.
            """
            
            response = model.generate_content(prompt)
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_text)
            self.after(0, lambda: self.render_ai_results(data))
        except Exception as e:
            self.after(0, lambda: self.lbl_ai_status.configure(text=f"AI Error: {e}"))

    def render_ai_results(self, data):
        self.lbl_ai_status.configure(text="Search Complete")
        for w in self.ai_results_frame.winfo_children(): w.destroy()
        
        for item in data:
            f = ctk.CTkFrame(self.ai_results_frame)
            f.pack(fill="x", pady=5)
            ctk.CTkLabel(f, text=item['rom'], font=("Arial", 14, "bold")).pack(side="left", padx=10)
            ctk.CTkButton(f, text="Open Link", width=80, command=lambda u=item['url']: webbrowser.open(u)).pack(side="right", padx=10)

    # --- DB LOGIC ---
    def load_databases(self):
        threading.Thread(target=self._load_db_thread, daemon=True).start()

    def _load_db_thread(self):
        try:
            r = requests.get(PIXELOS_API_URL)
            if r.status_code == 200:
                files = [x for x in r.json() if x['name'].endswith('.json')]
                with concurrent.futures.ThreadPoolExecutor() as exe:
                    futures = {exe.submit(requests.get, f['download_url']): f for f in files}
                    for fut in concurrent.futures.as_completed(futures):
                        try:
                            d = fut.result().json()
                            if d.get('active'):
                                n = f"{d['vendor']} {d['model']} ({d['codename']})"
                                self.pixelos_devices[n] = d['download_link']
                        except: continue
                
                sorted_list = sorted(self.pixelos_devices.keys())
                self.after(0, lambda: self.pixelos_dropdown.configure(values=sorted_list))
                if sorted_list: self.after(0, lambda: self.pixelos_dropdown.set(sorted_list[0]))
        except: pass
        
        try:
            r = requests.get(DEVICE_DB_URL)
            if r.status_code == 200:
                for d in r.json():
                    self.universal_devices[f"{d['brand']} {d['name']}"] = d['codename']
                self.after(0, lambda: self.filter_devices(None))
        except: pass

    # --- SEARCH LOGIC ---
    def filter_devices(self, event):
        query = self.search_entry.get().lower()
        for w in self.device_listbox.winfo_children(): w.destroy()
        
        count = 0
        for name, code in self.universal_devices.items():
            if query in name.lower() or query in code.lower():
                if count > 50: break
                ctk.CTkButton(self.device_listbox, text=f"{name} ({code})", anchor="w",
                              command=lambda n=name, c=code: self.search_roms(n, c),
                              fg_color="transparent", height=30).pack(fill="x")
                count += 1

    def search_roms(self, name, codename):
        for w in self.results_scroll.winfo_children(): w.destroy()
        ctk.CTkLabel(self.results_scroll, text=f"Results for {codename}:", font=("Arial", 14, "bold")).pack(anchor="w", pady=5)
        links = [
            ("Search XDA Forums", f"https://www.google.com/search?q=site:forum.xda-developers.com+{codename}+rom"),
            ("Search SourceForge", f"https://sourceforge.net/directory/?q={codename}+rom"),
            ("Search Telegram", f"https://t.me/s/{codename}_updates")
        ]
        for title, url in links:
            ctk.CTkButton(self.results_scroll, text=title, anchor="w", fg_color="transparent", border_width=1,
                          command=lambda u=url: webbrowser.open(u)).pack(fill="x", pady=2)

    # --- FLASHER CORE ---
    def select_manual_file(self):
        f = filedialog.askopenfilename()
        if f:
            self.manual_file = f
            self.lbl_manual.configure(text=os.path.basename(f), text_color="green")
            self.btn_manual_flash.configure(state="normal")

    def start_manual_flash(self):
        self.switch_frame(self.frame_home, self.btn_home)
        threading.Thread(target=self.run_install_process, args=(True,), daemon=True).start()

    def start_pixelos_install(self):
        selection = self.pixelos_dropdown.get()
        if selection in self.pixelos_devices:
            self.selected_device_data = {"url": self.pixelos_devices[selection], "codename": selection.split("(")[-1][:-1]}
            threading.Thread(target=self.run_install_process, args=(False,), daemon=True).start()

    def run_install_process(self, is_manual):
        try:
            self.log("Starting Installation Process...")
            zip_path = ""
            if is_manual:
                zip_path = self.manual_file
            else:
                code = self.selected_device_data['codename']
                zip_path = os.path.join(DOWNLOAD_DIR, f"PixelOS_{code}.zip")
                if not os.path.exists(zip_path):
                    self.download_file(self.selected_device_data['url'], zip_path)

            self.log("Extracting Payload...")
            extract_dir = os.path.join(DOWNLOAD_DIR, "extracted_temp")
            if os.path.exists(extract_dir): shutil.rmtree(extract_dir)
            self.run_cmd([PAYLOAD_DUMPER_PATH, "-o", extract_dir, zip_path])

            flash_dir = None
            for root, _, files in os.walk(extract_dir):
                if "boot.img" in files: flash_dir = root; break
            if not flash_dir: raise Exception("Extraction failed.")

            self.log("--- PHASE 1: BOOTLOADER ---")
            self.ensure_mode("bootloader")
            self.run_cmd([FASTBOOT_PATH, "-w"])
            
            for p in PARTITIONS_BOOTLOADER: self.flash_img(p, flash_dir)

            self.log("--- PHASE 2: FASTBOOTD ---")
            self.run_cmd([FASTBOOT_PATH, "reboot", "fastboot"])
            time.sleep(10)
            self.ensure_mode("fastboot")

            for p in PARTITIONS_FASTBOOTD: self.flash_img(p, flash_dir)

            self.log("Rebooting...")
            self.run_cmd([FASTBOOT_PATH, "reboot"])
            messagebox.showinfo("Success", "Installation Complete!")

        except Exception as e:
            self.log(f"Error: {e}")
            messagebox.showerror("Error", str(e))

    def flash_img(self, part, folder):
        p = os.path.join(folder, f"{part}.img")
        if os.path.exists(p) and os.path.getsize(p) > 0:
            self.log(f"Flashing {part}...")
            self.run_cmd([FASTBOOT_PATH, "flash", part, p])

    def ensure_mode(self, mode):
        self.log(f"Waiting for {mode}...")
        for i in range(15):
            out = self.run_cmd_output([FASTBOOT_PATH, "devices"])
            if "fastboot" in out: return
            time.sleep(1)
        self.run_cmd([ADB_PATH, "reboot", "bootloader"])
        time.sleep(5)

    def download_file(self, url, dest):
        self.log(f"Downloading {url}...")
        with requests.get(url, stream=True) as r:
            with open(dest, 'wb') as f:
                for chunk in r.iter_content(8192): f.write(chunk)

    def log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def run_cmd(self, cmd):
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
