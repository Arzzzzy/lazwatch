# Lazada Stock Monitor

A modular Python desktop application that monitors product stock on Lazada.  
It features a user-friendly GUI, automated email notifications, and two powerful scanning modes to help you track restocks or new product drops efficiently.

---

## Features

### Scan Modes Explained
#### Target Scan (Deep Mode)
- Paste specific product URLs (one per line).
- The app visits each page.
- Checks if “Add to Cart” or “Buy Now” is active.
- Sends an email immediately if stock is detected.

#### Best for:
- Waiting for a specific sold-out product to restock.

### Store Scan (Fast Mode)
- Paste a store URL.
- Add keywords (e.g., Pokemon, iPhone, Limited Edition).
- The app scans listings and detects new matching products.
- Sends an email when a new item appears.

#### Best for:
- Catching new product drops instantly.

### Email Notifications
- When stock is detected:
- You receive an email instantly.
- Subject line indicates alert type.
- Includes product URL and detection timestamp.

---

## Disclaimer
- This project is for educational purposes only.
- Automated scraping may violate Lazada’s Terms of Service.
- Use responsibly and at your own risk.

### The developer is not responsible for:
- Account bans
- IP restrictions
- Email account limitations


