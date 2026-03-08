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
        super().__init__(vault_path, check_interval=20)
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

                if browser.pages:
                    page = browser.pages[0]
                else:
                    page = browser.new_page()

                self.logger.info("[DEBUG] Navigating to WhatsApp Web...")
                page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(5000)

                # Check for QR code
                self.logger.info("[DEBUG] Checking login status...")
                qr_selectors = ['canvas[aria-label*="Scan"]', 'div[data-ref]', 'canvas']
                qr_found = False
                for selector in qr_selectors:
                    try:
                        qr_element = page.query_selector(selector)
                        if qr_element and qr_element.is_visible():
                            qr_found = True
                            break
                    except:
                        continue

                if qr_found:
                    self.logger.info("=" * 70)
                    self.logger.info("[ACTION REQUIRED] WhatsApp Web requires login!")
                    self.logger.info("[ACTION REQUIRED] Scan QR code in browser window")
                    self.logger.info("[ACTION REQUIRED] Waiting 90 seconds...")
                    self.logger.info("=" * 70)

                    login_successful = False
                    for selector in qr_selectors:
                        try:
                            page.wait_for_selector(selector, state="hidden", timeout=90000)
                            login_successful = True
                            break
                        except:
                            continue

                    if login_successful:
                        self.logger.info("[OK] Login successful!")
                        page.wait_for_timeout(10000)
                    else:
                        self.logger.error("[ERROR] Login timeout")
                        browser.close()
                        return []
                else:
                    self.logger.info("[OK] Already logged in")

                # Wait for chat list
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
                    self.logger.warning("[WARN] Could not confirm chat list loaded")

                # Wait for chats to fully load
                self.logger.info("[DEBUG] Waiting for WhatsApp to FULLY load...")
                page.wait_for_timeout(10000)

                # Scroll chat list to load all chats
                self.logger.info("[DEBUG] Scrolling chat list to load all chats...")
                try:
                    # Find chat list container
                    chat_list_elem = page.query_selector('#pane-side')
                    if chat_list_elem:
                        # Scroll down multiple times to load more chats
                        for i in range(5):
                            page.evaluate('''
                                const paneElem = document.querySelector("#pane-side");
                                if (paneElem) {
                                    paneElem.scrollTop = paneElem.scrollHeight;
                                }
                            ''')
                            page.wait_for_timeout(1000)
                        # Scroll back to top
                        page.evaluate('''
                            const paneElem = document.querySelector("#pane-side");
                            if (paneElem) {
                                paneElem.scrollTop = 0;
                            }
                        ''')
                        page.wait_for_timeout(1000)
                        self.logger.info("[DEBUG] Scrolling complete")
                    else:
                        self.logger.warning("[WARN] Could not find #pane-side element")
                except Exception as e:
                    self.logger.warning(f"[WARN] Could not scroll chat list: {e}")

                # Process unread chats using while loop with fresh queries
                self.logger.info("[DEBUG] Starting to process unread chats...")
                unread_checked = 0
                messages_with_keywords = 0
                max_checks = 5

                while unread_checked < max_checks:
                    try:
                        # Wait a bit before querying
                        page.wait_for_timeout(2000)

                        # Query fresh chat rows - use most reliable selector
                        chat_rows = []

                        # Try role="listitem" first (most reliable for WhatsApp)
                        try:
                            chat_rows = page.query_selector_all('div[role="listitem"]')
                            if chat_rows and len(chat_rows) > 0:
                                self.logger.info(f"[DEBUG] Found {len(chat_rows)} chats using div[role=\"listitem\"]")
                        except:
                            pass

                        # Fallback: try other selectors
                        if not chat_rows or len(chat_rows) == 0:
                            try:
                                chat_rows = page.query_selector_all('[data-testid="cell-frame-container"]')
                                if chat_rows and len(chat_rows) > 0:
                                    self.logger.info(f"[DEBUG] Found {len(chat_rows)} chats using data-testid")
                            except:
                                pass

                        if not chat_rows or len(chat_rows) == 0:
                            self.logger.info("[INFO] No chat rows found")
                            break

                        # Find ALL unread chats
                        unread_chats = []
                        for idx, chat_row in enumerate(chat_rows):
                            try:
                                has_unread = False

                                # Check for unread badge
                                try:
                                    unread_badge = chat_row.query_selector('span[aria-label*="unread"]')
                                    if unread_badge:
                                        has_unread = True
                                except:
                                    pass

                                # Check HTML for unread indicator
                                if not has_unread:
                                    try:
                                        chat_html = chat_row.inner_html()
                                        if 'unread' in chat_html.lower():
                                            has_unread = True
                                    except:
                                        pass

                                if has_unread:
                                    try:
                                        # Get chat name from first line of text
                                        chat_text = chat_row.inner_text()
                                        chat_name = chat_text.split('\n')[0][:50] if chat_text else f"Chat {idx+1}"

                                        unread_chats.append({
                                            'index': idx,
                                            'element': chat_row,
                                            'name': chat_name
                                        })
                                        self.logger.info(f"[DEBUG] Unread chat #{len(unread_chats)}: {chat_name}")
                                    except Exception as e:
                                        self.logger.warning(f"[WARN] Error getting chat name: {e}")
                            except Exception as e:
                                self.logger.warning(f"[WARN] Error checking chat {idx}: {e}")
                                continue

                        self.logger.info(f"[DEBUG] Total unread chats found: {len(unread_chats)}")

                        # Check if we've processed all unread chats
                        if unread_checked >= len(unread_chats):
                            self.logger.info(f"[INFO] All {len(unread_chats)} unread chats checked")
                            break

                        # Get target chat
                        target_chat_info = unread_chats[unread_checked]
                        unread_checked += 1

                        self.logger.info(f"[DEBUG] Opening unread chat {unread_checked}/{len(unread_chats)}: {target_chat_info['name']}")

                        # Click on target chat
                        target_chat_info['element'].click()
                        page.wait_for_timeout(4000)  # Wait longer for chat to load

                        # Extract sender name
                        sender_name = "WhatsApp Contact"
                        try:
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

                        # Extract messages
                        message_text = ""
                        try:
                            page.wait_for_timeout(2000)

                            message_selectors = [
                                'div[data-testid="msg-container"]',
                                'div.message-in span.selectable-text',
                                'div[class*="message"] span[dir="ltr"]'
                            ]

                            for selector in message_selectors:
                                message_elements = page.query_selector_all(selector)
                                if message_elements:
                                    recent_messages = message_elements[-5:] if len(message_elements) > 5 else message_elements
                                    message_texts = []
                                    for msg_elem in recent_messages:
                                        msg_text = msg_elem.inner_text().strip()
                                        if msg_text and len(msg_text) > 0:
                                            message_texts.append(msg_text)

                                    if message_texts:
                                        message_text = "\n".join(message_texts)
                                        break

                            if message_text:
                                self.logger.info(f"[DEBUG] Extracted message: {message_text[:200]}")
                            else:
                                self.logger.warning("[WARN] Could not extract message text")

                        except Exception as e:
                            self.logger.error(f"[ERROR] Error extracting messages: {e}")

                        # Check for keywords
                        if message_text:
                            message_text_lower = message_text.lower()
                            matched_keywords = [kw for kw in self.keywords if kw in message_text_lower]

                            if matched_keywords:
                                self.logger.info(f"[OK] Found keywords: {matched_keywords}")

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
                            else:
                                self.logger.info(f"[DEBUG] No keywords found in messages from {sender_name}")

                        # Go back to chat list
                        page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=30000)
                        page.wait_for_timeout(3000)

                        # Wait for chat list to reload
                        for selector in ['#pane-side', '[data-testid="chat-list"]', 'div[role="grid"]']:
                            try:
                                page.wait_for_selector(selector, timeout=10000)
                                break
                            except:
                                continue

                    except Exception as e:
                        self.logger.error(f"[ERROR] Error in chat processing loop: {e}")
                        import traceback
                        traceback.print_exc()
                        try:
                            page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=30000)
                            page.wait_for_timeout(3000)
                        except:
                            break

                self.logger.info(f"[INFO] Checked {unread_checked} unread chats, found {messages_with_keywords} with keywords")

                if messages_found:
                    self.logger.info(f"[OK] Found {len(messages_found)} actionable message(s)")
                else:
                    self.logger.info("[INFO] No actionable messages found")

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

**Message:**
{item['text']}

**Keywords Detected:** {', '.join(item['keywords'])}

## Suggested Action
- [ ] Draft a reply
"""
        path.write_text(content, encoding='utf-8')
        self.duplicate_tracker.mark_processed(item['id'])
        return path

if __name__ == "__main__":
    vault_p = project_root / "vault"
    WhatsAppWatcher(str(vault_p)).run()
