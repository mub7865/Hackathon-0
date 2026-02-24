import os
import sys
import time
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Correctly add the project root to the Python path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.watchers.base_watcher import BaseWatcher
from src.utils.duplicate_tracker import DuplicateTracker
from src.utils.logger import setup_logger

class WhatsAppWatcher(BaseWatcher):
    def __init__(self, vault_path: str):
        super().__init__(vault_path, check_interval=20) # Faster check
        self.base_dir = project_root
        self.session_path = self.base_dir / "sessions" / "wa_autonomous_v3"
        tracker_path = self.base_dir / "sessions" / "processed_ids" / "whatsapp_processed_ids.json"
        log_dir = self.base_dir / "vault" / "Logs"
        self.needs_action_path = self.base_dir / "vault" / "Needs_Action"

        tracker_path.parent.mkdir(parents=True, exist_ok=True)
        log_dir.mkdir(parents=True, exist_ok=True)
        self.needs_action_path.mkdir(parents=True, exist_ok=True)

        self.logger = setup_logger('whatsapp-watcher', log_dir)
        self.duplicate_tracker = DuplicateTracker(tracker_path)
        self.keywords = ['urgent', 'asap', 'invoice', 'payment', 'help', 'emergency', 'critical', 'meeting', 'test', 'bhai']

    def check_for_updates(self):
        messages_found = []
        try:
            with sync_playwright() as p:
                # Launch with better settings for session persistence
                self.logger.info("[DEBUG] Launching browser...")
                browser = p.chromium.launch_persistent_context(
                    self.session_path,
                    headless=False,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                        "--disable-gpu",
                        "--disable-features=IsolateOrigins,site-per-process"
                    ],
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )

                # Get or create page
                if browser.pages:
                    page = browser.pages[0]
                else:
                    page = browser.new_page()

                # Navigate to WhatsApp Web
                self.logger.info("[DEBUG] Navigating to WhatsApp Web...")
                page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=60000)

                # Wait for initial load
                page.wait_for_timeout(5000)

                # Check for QR code (multiple possible selectors)
                self.logger.info("[DEBUG] Checking login status...")
                qr_selectors = [
                    'canvas[aria-label*="Scan"]',
                    'div[data-ref]',  # QR code container
                    'canvas'  # Generic canvas (QR code)
                ]

                qr_found = False
                for selector in qr_selectors:
                    try:
                        qr_element = page.query_selector(selector)
                        if qr_element and qr_element.is_visible():
                            qr_found = True
                            self.logger.info(f"[DEBUG] QR code detected with selector: {selector}")
                            break
                    except:
                        continue

                if qr_found:
                    self.logger.info("=" * 70)
                    self.logger.info("[ACTION REQUIRED] WhatsApp Web requires login!")
                    self.logger.info("[ACTION REQUIRED] Steps to login:")
                    self.logger.info("[ACTION REQUIRED] 1. Open WhatsApp on your phone")
                    self.logger.info("[ACTION REQUIRED] 2. Tap Menu (⋮) or Settings")
                    self.logger.info("[ACTION REQUIRED] 3. Tap 'Linked Devices'")
                    self.logger.info("[ACTION REQUIRED] 4. Tap 'Link a Device'")
                    self.logger.info("[ACTION REQUIRED] 5. Scan the QR code in the browser window")
                    self.logger.info("[ACTION REQUIRED] Waiting 90 seconds for you to scan...")
                    self.logger.info("=" * 70)

                    # Wait for any of the QR selectors to disappear
                    login_successful = False
                    for selector in qr_selectors:
                        try:
                            page.wait_for_selector(selector, state="hidden", timeout=90000)
                            login_successful = True
                            break
                        except:
                            continue

                    if login_successful:
                        self.logger.info("[OK] Login successful! Session saved.")
                        page.wait_for_timeout(10000)  # Wait for chats to load
                    else:
                        self.logger.error("[ERROR] Login timeout - QR code not scanned")
                        browser.close()
                        return []
                else:
                    self.logger.info("[OK] Already logged in")

                # Wait for chat list with multiple selectors
                self.logger.info("[DEBUG] Waiting for chat list...")
                chat_list_loaded = False
                chat_selectors = ['#pane-side', '[data-testid="chat-list"]', 'div[role="grid"]']

                for selector in chat_selectors:
                    try:
                        page.wait_for_selector(selector, timeout=15000)
                        self.logger.info(f"[OK] Chat list loaded (selector: {selector})")
                        chat_list_loaded = True
                        break
                    except:
                        continue

                if not chat_list_loaded:
                    self.logger.warning("[WARN] Could not confirm chat list loaded, continuing...")

                # Wait for WhatsApp to FULLY load (not just DOM ready)
                self.logger.info("[DEBUG] Waiting for WhatsApp to FULLY load...")
                self.logger.info("[INFO] This may take 30-60 seconds, please wait...")

                # Wait for initial load
                page.wait_for_timeout(10000)

                # Wait for "Loading..." to disappear
                self.logger.info("[DEBUG] Waiting for chats to finish loading...")
                max_wait_time = 60  # 60 seconds max
                start_time = datetime.now()

                while (datetime.now() - start_time).seconds < max_wait_time:
                    try:
                        # Check if "Loading..." text is still present
                        page_text = page.inner_text('body')
                        loading_count = page_text.count('Loading')

                        self.logger.info(f"[DEBUG] Loading indicators found: {loading_count}")

                        if loading_count == 0:
                            self.logger.info("[OK] All chats loaded!")
                            break

                        # Wait 5 seconds before checking again
                        page.wait_for_timeout(5000)

                    except:
                        break

                # Additional wait to be safe
                page.wait_for_timeout(5000)

                # ROBUST APPROACH: Try multiple ways to find and read chats
                self.logger.info("[DEBUG] Looking for unread chats...")

                # Take screenshot for debugging
                screenshot_path = self.base_dir / "vault" / f"whatsapp_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                page.screenshot(path=str(screenshot_path))
                self.logger.info(f"[DEBUG] Screenshot saved: {screenshot_path}")

                # Try multiple selectors for chat rows
                chat_rows = []
                selectors_to_try = [
                    'div[role="listitem"]',
                    '[data-testid="cell-frame-container"]',
                    'div[data-testid^="cell-frame"]',
                    '#pane-side > div > div > div',  # Direct children of pane-side
                ]

                for selector in selectors_to_try:
                    try:
                        chat_rows = page.query_selector_all(selector)
                        if chat_rows:
                            self.logger.info(f"[OK] Found {len(chat_rows)} chats with selector: {selector}")
                            break
                    except:
                        continue

                if not chat_rows:
                    self.logger.warning("[WARN] Could not find chat rows with any selector")
                    self.logger.info("[INFO] Trying fallback: reading currently open conversation...")

                    # FALLBACK: Just read whatever conversation is currently open
                    try:
                        conversation_area = page.query_selector('div[role="application"]')
                        if conversation_area:
                            conv_text = conversation_area.inner_text()
                            self.logger.info(f"[DEBUG] Current conversation length: {len(conv_text)} chars")

                            if len(conv_text) > 100:
                                self.logger.info(f"[DEBUG] Conversation preview: {conv_text[:300]}")

                                # Check for keywords
                                conv_text_lower = conv_text.lower()
                                matched_keywords = [kw for kw in self.keywords if kw in conv_text_lower]

                                if matched_keywords:
                                    self.logger.info(f"[OK] Found keywords in open conversation: {matched_keywords}")

                                    keyword = matched_keywords[0]
                                    keyword_index = conv_text_lower.find(keyword)
                                    context_start = max(0, keyword_index - 100)
                                    context_end = min(len(conv_text), keyword_index + 300)
                                    context = conv_text[context_start:context_end]

                                    msg_id = f"wa_{keyword}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

                                    if not self.duplicate_tracker.is_duplicate(msg_id):
                                        messages_found.append({
                                            'id': msg_id,
                                            'sender': 'WhatsApp Contact',
                                            'text': context.strip(),
                                            'keywords': matched_keywords
                                        })
                                        self.duplicate_tracker.mark_processed(msg_id)
                                        self.logger.info(f"[OK] Message queued from open conversation")
                    except Exception as e:
                        self.logger.error(f"[ERROR] Fallback also failed: {e}")

                    browser.close()
                    return messages_found

                # Process chat rows
                self.logger.info(f"[DEBUG] Processing {len(chat_rows)} chats...")
                unread_checked = 0
                messages_with_keywords = 0

                for idx, chat_row in enumerate(chat_rows):
                    try:
                        # Check if this chat has unread indicator
                        has_unread = False

                        # Method 1: Look for unread badge
                        unread_badge = chat_row.query_selector('span[aria-label*="unread"]')
                        if unread_badge:
                            has_unread = True

                        # Method 2: Look for green dot or bold text (unread indicators)
                        if not has_unread:
                            chat_html = chat_row.inner_html()
                            if 'unread' in chat_html.lower():
                                has_unread = True

                        if not has_unread:
                            continue

                        unread_checked += 1
                        self.logger.info(f"[DEBUG] Checking unread chat {unread_checked}...")

                        # Click on chat to open it
                        chat_row.click()
                        page.wait_for_timeout(3000)

                        # Extract sender name from chat header
                        sender_name = "WhatsApp Contact"
                        try:
                            # Try multiple selectors for chat header
                            header_selectors = [
                                'header span[dir="auto"]',
                                'header [data-testid="conversation-info-header-chat-title"]',
                                'div[data-testid="conversation-panel-wrapper"] header span'
                            ]
                            for selector in header_selectors:
                                header_elem = page.query_selector(selector)
                                if header_elem:
                                    sender_name = header_elem.inner_text().strip()
                                    if sender_name:
                                        break
                            self.logger.info(f"[DEBUG] Sender: {sender_name}")
                        except Exception as e:
                            self.logger.warning(f"[WARN] Could not extract sender name: {e}")

                        # Extract messages from conversation
                        message_text = ""
                        try:
                            # Wait for messages to load
                            page.wait_for_timeout(2000)

                            # Try to find message bubbles
                            message_selectors = [
                                'div[data-testid="msg-container"]',
                                'div.message-in span.selectable-text',
                                'div[class*="message"] span[dir="ltr"]'
                            ]

                            for selector in message_selectors:
                                message_elements = page.query_selector_all(selector)
                                if message_elements:
                                    # Get last few messages (up to 5)
                                    recent_messages = message_elements[-5:] if len(message_elements) > 5 else message_elements
                                    message_texts = []
                                    for msg_elem in recent_messages:
                                        msg_text = msg_elem.inner_text().strip()
                                        if msg_text and len(msg_text) > 0:
                                            message_texts.append(msg_text)

                                    if message_texts:
                                        message_text = "\n".join(message_texts)
                                        break

                            if not message_text:
                                self.logger.warning("[WARN] Could not extract message text, skipping")
                                continue

                            self.logger.info(f"[DEBUG] Extracted message: {message_text[:200]}")

                        except Exception as e:
                            self.logger.error(f"[ERROR] Error extracting messages: {e}")
                            continue

                        # NOW check for keywords in the actual message text
                        message_text_lower = message_text.lower()
                        matched_keywords = [kw for kw in self.keywords if kw in message_text_lower]

                        if not matched_keywords:
                            self.logger.info(f"[DEBUG] No keywords found in messages from {sender_name}, skipping")
                            # Go back to chat list for next iteration
                            page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=30000)
                            page.wait_for_timeout(3000)
                            continue

                        self.logger.info(f"[OK] Found keywords in messages: {matched_keywords}")

                        # Create message object
                        msg_id = f"wa_{matched_keywords[0]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

                        if not self.duplicate_tracker.is_duplicate(msg_id):
                            messages_found.append({
                                'id': msg_id,
                                'sender': sender_name,
                                'text': message_text,
                                'keywords': matched_keywords
                            })
                            self.duplicate_tracker.mark_processed(msg_id)
                            messages_with_keywords += 1
                            self.logger.info(f"[OK] Message queued from {sender_name}")

                        # Go back to chat list for next iteration
                        page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=30000)
                        page.wait_for_timeout(3000)

                        # Limit to checking 5 unread chats
                        if unread_checked >= 5:
                            self.logger.info("[INFO] Checked 5 unread chats, stopping")
                            break

                    except Exception as e:
                        self.logger.error(f"[ERROR] Error processing chat {idx}: {e}")
                        import traceback
                        traceback.print_exc()
                        continue

                self.logger.info(f"[INFO] Checked {unread_checked} unread chats, found {messages_with_keywords} with keywords")

                if messages_found:
                    self.logger.info(f"[OK] Found {len(messages_found)} actionable message(s)")
                else:
                    self.logger.info("[INFO] No actionable messages found")

                # Close browser
                browser.close()
                self.logger.info("[DEBUG] Browser closed successfully")

        except Exception as e:
            self.logger.error(f"[ERROR] Watcher Error: {e}")
            import traceback
            traceback.print_exc()

        return messages_found

    def create_action_file(self, item):
        filename = f"WHATSAPP_{item['sender'].replace(' ', '_')}_{datetime.now().strftime('%H%M%S')}.md"
        path = self.needs_action_path / filename
        content = f"""---
id: {item['id']}
source: whatsapp
type: whatsapp
status: pending
priority: high
created: {datetime.now().isoformat()}
whatsapp_sender: "{item['sender']}"
---
## WhatsApp Message from {item['sender']}
**Text**: {item['text']}
**Keywords**: {', '.join(item['keywords'])}

## Suggested Action
- [ ] Draft a reply
"""
        path.write_text(content, encoding='utf-8')
        self.duplicate_tracker.mark_processed(item['id'])
        return path

if __name__ == "__main__":
    vault_p = project_root / "vault"
    WhatsAppWatcher(str(vault_p)).run()
