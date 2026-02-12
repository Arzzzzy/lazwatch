import os
import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
from datetime import datetime
from dotenv import load_dotenv

from app.monitor import run_monitor

# Load environment variables from .env file
load_dotenv()

# Global control variables
monitor_thread = None
stop_event = threading.Event()
GUI_LOG_WIDGET = None

def log_to_gui(message, color=None):
    """Callback function to update the GUI log from the monitor thread."""
    if GUI_LOG_WIDGET:
        tag = color if color else "default"
        timestamp = datetime.now().strftime('%H:%M:%S')
        full_msg = f"[{timestamp}] {message}\n"
        
        try:
            # Enable widget temporarily to write to it
            GUI_LOG_WIDGET.config(state=tk.NORMAL)
            GUI_LOG_WIDGET.insert(tk.END, full_msg, tag)
            GUI_LOG_WIDGET.see(tk.END)
            # Disable it again to make it read-only
            GUI_LOG_WIDGET.config(state=tk.DISABLED)
        except Exception:
            pass
            
    # Print to console as backup
    print(f"[{color}] {message}")

def start_monitor_action(mode, url_input, keyword_input, start_btn, stop_btn, email_entries):
    global monitor_thread, stop_event

    if monitor_thread and monitor_thread.is_alive():
        messagebox.showinfo("Info", "Monitor is already running.")
        return

    # --- 1. Validate Email Inputs ---
    sender_email = email_entries["sender_email"].get().strip()
    sender_password = email_entries["sender_password"].get().strip()
    
    recipients = []
    for key, entry in email_entries.items():
        if key.startswith("recipient"):
            val = entry.get().strip()
            if val:
                recipients.append(val)

    if not sender_email or not sender_password:
        messagebox.showerror("Missing Information", "Sender Email and App Password are required.")
        return

    if not recipients:
        messagebox.showerror("Missing Information", "You must enter at least one Recipient email.")
        return
        
    email_config = {
        "SENDER_EMAIL": sender_email,
        "SENDER_PASSWORD": sender_password,
        "RECIPIENT_EMAILS": recipients,
    }

    # --- 2. Validate Scan Inputs ---
    target_urls = []
    store_url = ""
    keywords = []

    if mode == 'target':
        urls_raw = url_input.get("1.0", tk.END).strip()
        if not urls_raw:
            messagebox.showerror("Missing Information", "Target URL list cannot be empty.")
            return

        target_urls = [u.strip() for u in urls_raw.split('\n') if u.strip()]
        if not target_urls:
            messagebox.showerror("Missing Information", "Please enter valid Target URLs.")
            return

    elif mode == 'store':
        store_url = url_input.get("1.0", tk.END).strip()
        if not store_url:
            messagebox.showerror("Missing Information", "Store URL cannot be empty.")
            return
            
        kw_raw = keyword_input.get("1.0", tk.END).strip()
        if not kw_raw:
             messagebox.showerror("Missing Information", "Keywords cannot be empty.")
             return

        keywords = [k.strip() for k in kw_raw.split('\n') if k.strip()]
        if not keywords:
            messagebox.showerror("Missing Information", "Please enter at least one valid keyword.")
            return

    # --- 3. Start Thread ---
    stop_event.clear()
    monitor_thread = threading.Thread(
        target=run_monitor, 
        args=(stop_event, mode, target_urls, store_url, keywords, email_config, log_to_gui)
    )
    monitor_thread.daemon = True
    monitor_thread.start()
    
    start_btn.config(state=tk.DISABLED)
    stop_btn.config(state=tk.NORMAL)

def stop_monitor_action(start_btn, stop_btn):
    global stop_event
    log_to_gui("Stopping monitor...", "red")
    stop_event.set()
    stop_btn.config(state=tk.DISABLED)
    start_btn.config(state=tk.NORMAL)

def create_gui():
    global GUI_LOG_WIDGET
    root = tk.Tk()
    root.title("Lazada Stock Monitor (Modular)")

    # --- INSTRUCTIONS SECTION ---
    instr_frame = tk.LabelFrame(root, text="ℹHow it Works", padx=10, pady=5, fg="blue")
    instr_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

    instr_text = (
        "1. TARGET SCAN: Monitors specific product links you provide. Use this to catch restocks.\n"
        "2. STORE SCAN: Monitors a shop's main page. Use this to find NEW items matching your keywords."
    )
    tk.Label(instr_frame, text=instr_text, justify=tk.LEFT, padx=5).pack(anchor="w")

    # --- Email Config ---
    email_frame = tk.LabelFrame(root, text="Email Configuration", padx=10, pady=5)
    email_frame.pack(fill=tk.X, padx=10, pady=5)
    
    email_entries = {}
    
    tk.Label(email_frame, text="Sender Email:").grid(row=0, column=0, sticky="w")
    e_sender = tk.Entry(email_frame, width=35)
    e_sender.insert(0, os.getenv("SENDER_EMAIL", ""))
    e_sender.grid(row=0, column=1, padx=5, pady=2)
    email_entries["sender_email"] = e_sender
    
    tk.Label(email_frame, text="App Password:").grid(row=1, column=0, sticky="w")
    e_pass = tk.Entry(email_frame, width=35, show="*")
    e_pass.insert(0, os.getenv("SENDER_PASSWORD", ""))
    e_pass.grid(row=1, column=1, padx=5, pady=2)
    email_entries["sender_password"] = e_pass

    tk.Label(email_frame, text="Recipients:").grid(row=2, column=0, sticky="nw", pady=5)
    recip_frame = tk.Frame(email_frame)
    recip_frame.grid(row=2, column=1, sticky="w")
    
    tk.Label(recip_frame, text="Emails below will receive alerts when a product matches.", fg="gray", font=("Arial", 8, "italic")).pack(anchor="w", pady=(0, 2))

    env_recipients = os.getenv("RECIPIENTS", "").split(",")
    env_recipients = [r.strip() for r in env_recipients if r.strip()]
    
    for i in range(3):
        e = tk.Entry(recip_frame, width=35)
        if i < len(env_recipients):
            e.insert(0, env_recipients[i])
        e.pack(pady=1)
        email_entries[f"recipient_{i+1}"] = e

    # --- Scan Mode ---
    mode_var = tk.StringVar(value='store')
    mode_frame = tk.LabelFrame(root, text="Scan Mode & Inputs", padx=10, pady=5)
    mode_frame.pack(fill=tk.X, padx=10, pady=5)

    # --- IMPORTANT INPUT LABEL ---
    tk.Label(mode_frame, text="ENTER URL & KEYWORDS HERE", fg="red", font=("Arial", 10, "bold")).pack(pady=(0, 5))

    url_label = tk.Label(mode_frame, text="Store URL:")
    url_input = scrolledtext.ScrolledText(mode_frame, height=4, width=60)
    
    default_store = os.getenv("DEFAULT_STORE_URL", "")
    default_targets = os.getenv("DEFAULT_TARGET_URLS", "").replace(",", "\n")

    kw_frame = tk.Frame(mode_frame) # Using Frame instead of LabelFrame for cleaner look inside
    kw_label = tk.Label(kw_frame, text="Keywords (One per line):")
    kw_input = scrolledtext.ScrolledText(kw_frame, height=4, width=60)

    def update_ui():
        # Hide everything first
        url_input.pack_forget()
        kw_frame.pack_forget()
        url_label.pack_forget()
        
        # Show mode selection radio buttons
        radio_frame.pack(fill=tk.X, pady=(0, 10))

        if mode_var.get() == 'target':
            url_label.config(text="Target Product URLs (One per line):")
            url_label.pack(anchor="w", padx=5)
            url_input.pack(fill=tk.X, padx=5, pady=2)
            
            # Refill with defaults if empty/changed
            if not url_input.get("1.0", tk.END).strip():
                url_input.insert(tk.END, default_targets)
        else:
            url_label.config(text="Store Page URL:")
            url_label.pack(anchor="w", padx=5)
            url_input.pack(fill=tk.X, padx=5, pady=2)
            
            kw_frame.pack(fill=tk.X, pady=5)
            kw_label.pack(anchor="w", padx=5)
            kw_input.pack(fill=tk.X, padx=5)

            if not url_input.get("1.0", tk.END).strip():
                 url_input.insert(tk.END, default_store)

    radio_frame = tk.Frame(mode_frame)
    tk.Radiobutton(radio_frame, text="Target Scan (Deep)", variable=mode_var, value='target', command=update_ui).pack(side=tk.LEFT, padx=10)
    tk.Radiobutton(radio_frame, text="Store Scan (Fast)", variable=mode_var, value='store', command=update_ui).pack(side=tk.LEFT, padx=10)
    radio_frame.pack(fill=tk.X)

    # --- Controls ---
    btn_frame = tk.Frame(root, pady=10)
    btn_frame.pack(fill=tk.X, padx=10)
    
    start_btn = tk.Button(btn_frame, text="START MONITOR", bg="green", fg="white", font=("Arial", 10, "bold"),
                          command=lambda: start_monitor_action(mode_var.get(), url_input, kw_input, start_btn, stop_btn, email_entries))
    start_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
    
    stop_btn = tk.Button(btn_frame, text="STOP MONITOR", bg="red", fg="white", font=("Arial", 10, "bold"), state=tk.DISABLED,
                         command=lambda: stop_monitor_action(start_btn, stop_btn))
    stop_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

    # --- Logs ---
    tk.Label(root, text="Monitor Log (Read-Only):", font=("Arial", 9, "bold")).pack(anchor="w", padx=10)
    GUI_LOG_WIDGET = scrolledtext.ScrolledText(root, height=12, state=tk.DISABLED) # <--- DISABLED BY DEFAULT
    GUI_LOG_WIDGET.tag_config('red', foreground='red')
    GUI_LOG_WIDGET.tag_config('green', foreground='green')
    GUI_LOG_WIDGET.tag_config('blue', foreground='blue')
    GUI_LOG_WIDGET.tag_config('yellow', foreground='dark orange')
    GUI_LOG_WIDGET.tag_config('cyan', foreground='cyan')
    GUI_LOG_WIDGET.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    update_ui()
    
    root.protocol("WM_DELETE_WINDOW", lambda: (stop_monitor_action(start_btn, stop_btn), root.destroy()))
    root.mainloop()

if __name__ == "__main__":
    create_gui()