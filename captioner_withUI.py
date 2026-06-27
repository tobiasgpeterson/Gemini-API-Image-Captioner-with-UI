#build .exe with:
#python -m PyInstaller --onefile --windowed --collect-all google --copy-metadata google-genai captioner_withUI.py
#make sure .venv is active

#generated using ai slop, output verified by real programmer TM

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from google import genai
from google.genai import types
from PIL import Image
import os
import threading
import time
import json

# --- CONSTANTS ---
CONFIG_FILE = "caption_config.json"

# Updated with the latest widely known models, keeping the futuristic ones at the top.
MODEL_OPTIONS = [
    "gemini-pro-latest",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-3-flash-preview",
    "gemini-3.1-pro-preview",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite-preview-02-05",
    "gemini-2.0-pro-exp-02-05",
    "gemini-1.5-flash",
    "gemini-1.5-pro"
]

DEFAULT_SYSTEM_INSTRUCTION = """"""

DEFAULT_PROMPT = """Describe this image in detail.
Do not generate title or chapter headings or needless confirmations such as "Of course." Only generate the description in a single continuous line.
Do not describe the art style or the medium of the image. Example: You don't need to describe the image as "a painting of an anime woman", or "photograph of a woman", just do "a woman..."
"""

DEFAULT_KEYS_HINT = """
AIzaSyCInsertYourFirstAPIKeyHere
AIzaSyCInsertYourSecondAPIKeyHere
AIzaSyCInsertYourThirdAPIKeyHere
"""

class CaptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gemini Image Captioner v2.3 (New SDK Compatible)")
        self.root.geometry("600x1100")
        
        # Styles
        style = ttk.Style()
        style.configure("Green.TButton", foreground="green", font=('Helvetica', 10, 'bold'))

        # --- UI LAYOUT ---
        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 1. API KEYS
        lbl_keys = tk.Label(main_frame, text="API Keys", font=("Arial", 10, "bold"), anchor="w")
        lbl_keys.pack(fill=tk.X, pady=(0, 2))
        
        lbl_keys_explainer = tk.Label(main_frame, text="This program will use the first Gemini API Key until the free tier usage limit has been exhausted, it will then move to the second key and use that until it is exhausted, etc. logic: Cycle Keys -> If all fail -> Switch Model -> Cycle Keys.", anchor="w", justify=tk.LEFT, wraplength=580)
        lbl_keys_explainer.pack(fill=tk.X)

        self.txt_api_keys = scrolledtext.ScrolledText(main_frame, height=4, font=("Consolas", 9))
        self.txt_api_keys.pack(fill=tk.X, pady=5)
        
        # 2. FOLDER PATH
        lbl_path = tk.Label(main_frame, text="Path to Folder Containing Images", font=("Arial", 10, "bold"), anchor="w")
        lbl_path.pack(fill=tk.X, pady=(10, 2))
        
        path_frame = tk.Frame(main_frame)
        path_frame.pack(fill=tk.X, pady=5)
        
        self.entry_path = tk.Entry(path_frame)
        self.entry_path.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        btn_browse = tk.Button(path_frame, text="Browse", command=self.browse_folder)
        btn_browse.pack(side=tk.RIGHT)

        # 3. SYSTEM INSTRUCTIONS
        lbl_sys_instr = tk.Label(main_frame, text="System Instructions (Context/Persona)", font=("Arial", 10, "bold"), anchor="w")
        lbl_sys_instr.pack(fill=tk.X, pady=(10, 2))

        self.txt_sys_instruction = scrolledtext.ScrolledText(main_frame, height=4, font=("Arial", 9))
        self.txt_sys_instruction.pack(fill=tk.X, pady=5)

        # 4. PROMPT
        lbl_prompt = tk.Label(main_frame, text="User Prompt (Task)", font=("Arial", 10, "bold"), anchor="w")
        lbl_prompt.pack(fill=tk.X, pady=(10, 2))

        self.txt_prompt = scrolledtext.ScrolledText(main_frame, height=5, font=("Arial", 9))
        self.txt_prompt.pack(fill=tk.X, pady=5)

        # 5. CUSTOM MODELS
        lbl_custom_models = tk.Label(main_frame, text="Custom Models to Try First (One per line, Optional)", font=("Arial", 10, "bold"), anchor="w")
        lbl_custom_models.pack(fill=tk.X, pady=(10, 2))
        lbl_custom_explainer = tk.Label(main_frame, text="These model IDs will be used FIRST in order. If they hit a limit or fail, it will fall back to the dropdown.", anchor="w", justify=tk.LEFT, wraplength=580)
        lbl_custom_explainer.pack(fill=tk.X)

        self.txt_custom_models = scrolledtext.ScrolledText(main_frame, height=3, font=("Consolas", 9))
        self.txt_custom_models.pack(fill=tk.X, pady=5)

        # 6. MODEL FALLBACK
        lbl_model = tk.Label(main_frame, text="Dropdown Fallback Model", font=("Arial", 10, "bold"), anchor="w")
        lbl_model.pack(fill=tk.X, pady=(10, 2))

        self.combo_model = ttk.Combobox(main_frame, values=MODEL_OPTIONS)
        self.combo_model.pack(fill=tk.X, pady=5)

        # 7. START BUTTON
        self.btn_start = tk.Button(main_frame, text="Start Captioning (Saves Config)", bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), command=self.start_thread)
        self.btn_start.pack(fill=tk.X, pady=15)

        # 8. LOG
        lbl_log = tk.Label(main_frame, text="Log", font=("Arial", 10, "bold"), anchor="w")
        lbl_log.pack(fill=tk.X, pady=(0, 2))

        self.txt_log = scrolledtext.ScrolledText(main_frame, height=10, state='disabled', bg="#f0f0f0", font=("Consolas", 8))
        self.txt_log.pack(fill=tk.BOTH, expand=True)

        # State variable
        self.is_running = False

        # --- LOAD CONFIG ON STARTUP ---
        self.load_config()

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.entry_path.delete(0, tk.END)
            self.entry_path.insert(0, folder_selected)

    def log(self, message):
        """Thread-safe logging"""
        self.txt_log.config(state='normal')
        self.txt_log.insert(tk.END, message + "\n")
        self.txt_log.see(tk.END)
        self.txt_log.config(state='disabled')
        self.root.update_idletasks()

    # --- CONFIGURATION HANDLERS ---
    def load_config(self):
        """Loads settings from JSON file or sets defaults."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Set keys
                self.txt_api_keys.delete('1.0', tk.END)
                keys = data.get('api_keys', DEFAULT_KEYS_HINT)
                if isinstance(keys, list):
                    self.txt_api_keys.insert(tk.END, "\n".join(keys))
                else:
                    self.txt_api_keys.insert(tk.END, keys)

                # Set Path
                self.entry_path.delete(0, tk.END)
                self.entry_path.insert(0, data.get('folder_path', ''))

                # Set System Instruction
                self.txt_sys_instruction.delete('1.0', tk.END)
                self.txt_sys_instruction.insert(tk.END, data.get('system_instruction', DEFAULT_SYSTEM_INSTRUCTION))

                # Set Prompt
                self.txt_prompt.delete('1.0', tk.END)
                self.txt_prompt.insert(tk.END, data.get('prompt', DEFAULT_PROMPT))

                # Set Custom Models
                self.txt_custom_models.delete('1.0', tk.END)
                self.txt_custom_models.insert(tk.END, data.get('custom_models', ''))

                # Set Model
                saved_model = data.get('model', MODEL_OPTIONS[0])
                if saved_model in MODEL_OPTIONS:
                    self.combo_model.set(saved_model)
                else:
                    self.combo_model.current(0)
                    
                self.log("✅ Configuration loaded.")
            except Exception as e:
                self.log(f"⚠️ Error loading config: {e}")
                self.set_defaults()
        else:
            self.set_defaults()

    def set_defaults(self):
        self.txt_api_keys.insert(tk.END, DEFAULT_KEYS_HINT)
        self.txt_sys_instruction.insert(tk.END, DEFAULT_SYSTEM_INSTRUCTION)
        self.txt_prompt.insert(tk.END, DEFAULT_PROMPT)
        self.combo_model.current(0)

    def save_config(self, api_keys_list, folder_path, sys_instruction, prompt, custom_models_text, model):
        """Saves current UI settings to JSON."""
        data = {
            "api_keys": api_keys_list,
            "folder_path": folder_path,
            "system_instruction": sys_instruction,
            "prompt": prompt,
            "custom_models": custom_models_text,
            "model": model
        }
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            self.log(f"⚠️ Could not save config: {e}")

    # --- PROCESSING LOGIC ---
    def start_thread(self):
        if self.is_running: return
        
        # Gather inputs
        raw_keys = self.txt_api_keys.get("1.0", tk.END).strip()
        api_keys = [k.strip() for k in raw_keys.split('\n') if k.strip()]
        folder_path = self.entry_path.get().strip()
        
        sys_instruction_text = self.txt_sys_instruction.get("1.0", tk.END).strip()
        prompt_text = self.txt_prompt.get("1.0", tk.END).strip()
        
        custom_models_text = self.txt_custom_models.get("1.0", tk.END).strip()
        start_model_name = self.combo_model.get()

        # Validation
        if not api_keys or (len(api_keys) == 1 and api_keys[0].startswith("AIzaSyCw...")):
            messagebox.showerror("Error", "Please enter valid API Keys.")
            return
        if not os.path.isdir(folder_path):
            messagebox.showerror("Error", "Invalid Folder Path.")
            return

        # Save config before starting
        self.save_config(api_keys, folder_path, sys_instruction_text, prompt_text, custom_models_text, start_model_name)

        self.is_running = True
        self.btn_start.config(state='disabled', text="Processing...")
        
        thread = threading.Thread(
            target=self.process_images, 
            args=(api_keys, folder_path, sys_instruction_text, prompt_text, custom_models_text, start_model_name)
        )
        thread.daemon = True
        thread.start()

    def create_client(self, api_key):
        """Helper to set up the new Google GenAI Client"""
        try:
            client = genai.Client(api_key=api_key)
            return client
        except Exception as e:
            self.log(f"⚠️ SDK Client Error: {e}")
            return None

    def process_images(self, api_keys, folder_path, sys_instruction_text, prompt_text, custom_models_text, start_model_name):
        self.log(f"--- Starting Process ---")
        
        # 1. Parse custom models from the multiline text box
        custom_models_list = [m.strip() for m in custom_models_text.split('\n') if m.strip()]
        
        # 2. Determine dropdown fallback models (Starting from the user's dropdown selection)
        try:
            dropdown_start_index = MODEL_OPTIONS.index(start_model_name)
        except ValueError:
            dropdown_start_index = 0
        fallback_models_list = MODEL_OPTIONS[dropdown_start_index:]
        
        # 3. Combine both lists (Deduplicate while preserving order)
        all_models_to_try = []
        for m in custom_models_list + fallback_models_list:
            if m not in all_models_to_try:
                all_models_to_try.append(m)

        if not all_models_to_try:
            self.log("🛑 CRITICAL: No models available to process.")
            self.reset_ui()
            return

        current_key_index = 0
        current_model_idx = 0
        
        # Initial Configuration
        active_model_name = all_models_to_try[current_model_idx]
        active_key = api_keys[current_key_index]
        
        client = self.create_client(active_key)
        if not client:
            self.log("🛑 CRITICAL: Failed to initialize API Client.")
            self.reset_ui()
            return
        
        self.log(f"🔹 Active Model: {active_model_name}")
        self.log(f"🔑 Active Key: #{current_key_index + 1}")

        # Get Images
        supported_extensions = ('.png', '.jpg', '.jpeg', '.webp')
        try:
            image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(supported_extensions)]
        except Exception as e:
            self.log(f"🛑 Error reading folder: {e}")
            self.reset_ui()
            return

        if not image_files:
            self.log("⚠️ No images found in folder.")
            self.reset_ui()
            return

        processed_count = 0

        for filename in image_files:
            if not self.is_running: break 

            image_path = os.path.join(folder_path, filename)
            base_filename, _ = os.path.splitext(filename)
            caption_path = os.path.join(folder_path, f"{base_filename}.txt")

            if os.path.exists(caption_path):
                self.log(f"⏭️ Skipping '{filename}' (exists).")
                continue

            # --- RETRY LOOP FOR CURRENT IMAGE ---
            while True:
                try:
                    self.log(f"⏳ Processing '{filename}'...")
                    img = Image.open(image_path)
                    
                    # --- NEW SDK GENERATION CALL ---
                    # 1. Setup config (equivalent of the old safety settings + system prompt)
                    config_args = {
                        "safety_settings": [
                            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
                        ]
                    }
                    if sys_instruction_text:
                        config_args["system_instruction"] = sys_instruction_text

                    config = types.GenerateContentConfig(**config_args)

                    # 2. Make the API Call directly using client.models.generate_content
                    response = client.models.generate_content(
                        model=active_model_name,
                        contents=[prompt_text, img],
                        config=config
                    )

                    caption = response.text.strip().replace('\n', ' ')

                    with open(caption_path, 'w', encoding='utf-8') as f:
                        f.write(caption)
                    
                    self.log(f"✅ Success: '{filename}'")
                    processed_count += 1
                    break # Break retry loop, move to next image

                except Exception as e:
                    error_str = str(e).lower()
                    
                    # 1. Check for Quota/Limits
                    if "429" in error_str or "resourceexhausted" in error_str or "quota exceeded" in error_str:
                        self.log(f"⚠️ Limit hit on Key #{current_key_index + 1} ({active_model_name})")
                        
                        current_key_index += 1
                        
                        # If Keys Exhausted, Switch Model and Reset Keys
                        if current_key_index >= len(api_keys):
                            self.log(f"🔻 All keys exhausted for {active_model_name}.")
                            current_key_index = 0 # Reset to first key
                            current_model_idx += 1 # Move to next model

                            if current_model_idx >= len(all_models_to_try):
                                self.log("🛑 CRITICAL: All Models and All Keys exhausted. Stopping.")
                                self.reset_ui()
                                return
                            
                            active_model_name = all_models_to_try[current_model_idx]
                            self.log(f"🔄 SWITCHING MODEL to: {active_model_name}")
                        else:
                            self.log(f"🔄 Switching to Key #{current_key_index + 1}")

                        active_key = api_keys[current_key_index]
                        client = self.create_client(active_key)
                        time.sleep(2) 
                        continue 
                    
                    # 2. Check for invalid or non-existent model (e.g., user made a typo in the custom textbox)
                    elif "not found" in error_str or "invalid" in error_str:
                        self.log(f"⚠️ Model '{active_model_name}' invalid/not found. Skipping model...")
                        current_key_index = 0
                        current_model_idx += 1
                        
                        if current_model_idx >= len(all_models_to_try):
                            self.log("🛑 CRITICAL: Run out of valid models. Stopping.")
                            self.reset_ui()
                            return
                        
                        active_model_name = all_models_to_try[current_model_idx]
                        self.log(f"🔄 SWITCHING MODEL to: {active_model_name}")
                        
                        active_key = api_keys[current_key_index]
                        client = self.create_client(active_key)
                        time.sleep(1)
                        continue

                    # 3. Other errors (corrupt image, API timeouts, etc)
                    else:
                        self.log(f"❌ Error on '{filename}': {e}")
                        break # Skip image

        self.log(f"\n🎉 Finished! Total processed: {processed_count}")
        self.reset_ui()

    def reset_ui(self):
        self.is_running = False
        self.btn_start.config(state='normal', text="Start Captioning (Saves Config)")


if __name__ == "__main__":
    root = tk.Tk()
    app = CaptionApp(root)
    root.mainloop()
