import time
import random
import re
from selenium.webdriver.common.by import By

# REMOVED 'log_to_gui' from this import list
from app.utils import (
    setup_driver, load_seen, save_seen, now_iso, play_alarm, 
    human_like_wait, human_like_scroll, normalize_title
)
from app.email_service import send_notification_email

def is_sold_out_text(card_text: str):
    card_text = (card_text or "").lower()
    return any(x in card_text for x in ["sold out", "out of stock", "no stock", "unavailable", "temporarily unavailable"])

def title_matches_any_keyword(text: str, keywords: list):
    text = (text or "").lower()
    return any(kw.lower() in text for kw in keywords)

def extract_title_and_url(card):
    title = ""
    url = ""
    try:
        link = card.find_element(By.CSS_SELECTOR, "a[href*='/products/'], a[href*='/product/']")
        url = link.get_attribute("href") or ""
        title = (link.text or "").strip()
        if not title:
            img = card.find_element(By.CSS_SELECTOR, "img")
            title = img.get_attribute("alt") or img.get_attribute("title") or ""
    except Exception:
        pass
    return title or "Unknown Title", url or ""

def check_product_availability_lazada(url: str, driver) -> bool:
    if not url: return None
    try:
        if re.search(r"(?:[?&]|%3F|%26)stock(?:=|%3D)0", url, re.IGNORECASE):
            return False
        driver.get(url)
        time.sleep(random.uniform(2.0, 4.0))
        page_src = driver.page_source.lower()

        m = re.search(r'"stock"\s*:\s*(\d+)', page_src)
        if m:
            return int(m.group(1)) > 0

        if any(x in page_src for x in ['"issoldout":true', '"is_sold_out":true', '"available":false']):
            return False
        
        # Check Buttons
        buy_keywords = ["add to cart", "buy now", "add to bag", "purchase", "checkout", "buy"]
        sold_keywords = ["sold out", "out of stock", "notify me", "unavailable"]

        candidates = driver.find_elements(By.XPATH, "//button | //a[@role='button'] | //input[@type='button']")
        for el in candidates:
            try:
                if not el.is_displayed(): continue
                txt = (el.text or el.get_attribute("value") or "").strip().lower()
                if not txt:
                    txt = driver.execute_script("return arguments[0].innerText;", el).strip().lower()
                
                if (el.get_attribute("disabled") or "").lower() in ("true", "disabled"): continue

                if any(k in txt for k in buy_keywords): return True
                if any(k in txt for k in sold_keywords): return False
            except Exception: continue
            
        return None
    except Exception:
        return None

def run_monitor(stop_event, scan_mode, target_urls, store_url, keywords, email_config, log_callback):
    if log_callback:
        log_callback(f"Starting monitor in **{scan_mode.upper()}** mode.", "blue")
    
    seen = load_seen()
    driver = setup_driver(headless=False, log_callback=log_callback)
    if not driver:
        return

    while not stop_event.is_set():
        try:
            # --- TARGET MODE ---
            if scan_mode == 'target':
                if log_callback: log_callback(f"\nChecking {len(target_urls)} target URL(s)...", "blue")
                
                for target_url in target_urls:
                    if stop_event.is_set(): break
                    try:
                        match = re.search(r'pdp-i(\d+)\.html', target_url)
                        title_key = f"target_{match.group(1)}" if match else f"target_{hash(target_url)}"
                        title = f"[TARGET] Product ID {match.group(1)}" if match else f"[TARGET] {target_url.split('/')[-1]}"
                        
                        is_new_listing = title_key not in seen
                        if log_callback: log_callback(f"* Deep checking: {title}...", "cyan")
                        
                        page_avail = check_product_availability_lazada(target_url, driver)
                        now = now_iso()

                        sold_out = True
                        if page_avail is True: sold_out = False
                        elif page_avail is False: sold_out = True
                        
                        # Save Data
                        if is_new_listing:
                            seen[title_key] = {"title": title, "url": target_url, "first_seen": now, "last_seen": now, "sold_out": sold_out}
                        else:
                            seen[title_key].update({"last_seen": now, "sold_out": sold_out})
                        save_seen(seen, log_callback)

                        # Notify if IN STOCK
                        if not sold_out:
                            subject = f"AVAILABLE: {title} @ {now}"
                            body = f"Target product IN STOCK!\n\nTitle: {title}\nTime: {now}\nURL: {target_url}"
                            send_notification_email(subject, body, email_config, log_callback)
                            if log_callback: log_callback(f"!!! READY TO BUY !!! {title}", "green")
                            play_alarm(log_callback)
                        else:
                            if log_callback: log_callback(f":: OUT OF STOCK :: {title}", "red")

                    except Exception as e:
                        if log_callback: log_callback(f"Error checking target: {e}", "red")

                if not stop_event.is_set():
                    human_like_wait(min_sec=10, max_sec=20, log_callback=log_callback)

            # --- STORE MODE ---
            elif scan_mode == 'store':
                if log_callback: log_callback(f"\nChecking store URL (Fast Scan)...", "blue")
                try:
                    driver.get(store_url)
                    time.sleep(random.uniform(2, 4))
                except Exception as e:
                    if log_callback: log_callback(f"Nav Error: {e}", "red")
                    continue

                product_cards = driver.find_elements(By.CSS_SELECTOR, "div[data-tracking='product-card'], div[data-qa-locator='productItem'], div.c2prKC")
                new_items_found = 0

                for card in product_cards:
                    if stop_event.is_set(): break
                    try:
                        card_text = card.text or ""
                        if not title_matches_any_keyword(card_text, keywords): continue

                        title, url = extract_title_and_url(card)
                        if not url: continue

                        title_key = normalize_title(title)
                        now = now_iso()

                        if title_key not in seen:
                            # New Item Found
                            new_items_found += 1
                            seen[title_key] = {"title": title, "url": url, "first_seen": now, "last_seen": now, "sold_out": False}
                            save_seen(seen, log_callback)
                            
                            subject = f"NEW LISTING: {title}"
                            body = f"NEW product detected!\n\nTitle: {title}\nTime: {now}\nURL: {url}"
                            send_notification_email(subject, body, email_config, log_callback)
                            
                            if log_callback: log_callback(f"!!! NEW LISTING !!! {title}", "green")
                            play_alarm(log_callback)
                            break # Break to refresh immediately
                        else:
                             seen[title_key].update({"last_seen": now})
                             save_seen(seen, log_callback)
                             if log_callback: log_callback(f"Tracking: {title}", "default")

                    except Exception: continue
                
                if new_items_found > 0:
                     if log_callback: log_callback("New item found, re-scanning immediately...", "blue")
                elif not stop_event.is_set():
                    human_like_scroll(driver)
                    human_like_wait(min_sec=8, max_sec=15, log_callback=log_callback)

        except Exception as e:
            if log_callback: log_callback(f"Loop error: {e}", "red")
            if not stop_event.is_set(): human_like_wait(10, 20)

    if log_callback: log_callback("Monitor stopped. Closing browser.", "blue")
    driver.quit()