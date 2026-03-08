import os
import sys
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright
import hashlib

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.watchers.base_watcher import BaseWatcher
from src.utils.duplicate_tracker import DuplicateTracker
from src.utils.logger import setup_logger

class WhatsAppWatcher(BaseWatcher):
    def __init__(self, vault_path: str):
        super().__init__(vault_path, check_interval=20)
        self.base_dir = project_root
        self.session_path = self.base_dir / "sessions" / "wa_fresh"
        tracker_path = self.base_dir / "sessions" / "processed_ids" / "whatsapp_processed_ids.json"
        log_dir = self.base_dir / "vault" / "Logs"
        self.needs_action_path = self.base_dir / "vault" / "Needs_Action"

        tracker_path.parent.mkdir(parents=True, exist_ok=True)
        log_dir.mkdir(parents=True, exist_ok=True)
        self.needs_action_path.mkdir(parents=True, exist_ok=True)

        self.logger = setup_logger('whatsapp-watcher', log_dir)
        self.duplicate_tracker = DuplicateTracker(tracker_path)
        self.keywords = ['urgent', 'asap', 'invoice', 'payment', 'help', 'emergency', 'critical', 'meeting']

    def check_for_updates(self):
        messages_found = []

        # Check if action has lock - if so, skip this cycle
        lock_file = self.base_dir / "sessions" / "wa_action.lock"
        if lock_file.exists():
            self.logger.info("[INFO] Action lock detected - skipping this cycle")
            return messages_found

        try:
            with sync_playwright() as p:
                self.logger.info("[INFO] Starting WhatsApp watcher...")

                browser = p.chromium.launch_persistent_context(
                    self.session_path,
                    headless=False
                )

                page = browser.pages[0] if browser.pages else browser.new_page()
                page.goto("https://web.whatsapp.com")

                self.logger.info("[INFO] Waiting for WhatsApp to load...")
                self.logger.info("[INFO] If you see QR code, please scan it now...")
                self.logger.info("[INFO] Waiting 60 seconds for login/load...")

                # Wait up to 60 seconds for chat list to appear (allows time for QR scan if needed)
                try:
                    page.wait_for_selector('#pane-side', timeout=60000)
                    self.logger.info("[OK] Chat pane loaded successfully")
                except:
                    # Take screenshot to see what's wrong
                    screenshot_path = self.base_dir / "vault" / f"wa_error_{datetime.now().strftime('%H%M%S')}.png"
                    page.screenshot(path=str(screenshot_path))
                    self.logger.error(f"[ERROR] Chat pane did not load. Screenshot: {screenshot_path}")
                    self.logger.error("[ERROR] Please check if WhatsApp Web is logged in")

                    # Keep browser open for 30 seconds so user can see what's wrong
                    self.logger.info("[INFO] Keeping browser open for 30 seconds for inspection...")
                    page.wait_for_timeout(30000)
                    browser.close()
                    return messages_found

                # Additional wait for chats to fully load
                page.wait_for_timeout(5000)

                # Take screenshot for debugging
                screenshot_path = self.base_dir / "vault" / f"wa_debug_{datetime.now().strftime('%H%M%S')}.png"
                page.screenshot(path=str(screenshot_path))
                self.logger.info(f"[DEBUG] Screenshot saved: {screenshot_path}")

                # Find all chat elements - try multiple selectors
                self.logger.info("[INFO] Finding unread chats...")

                # Try different selectors for WhatsApp Web
                chat_elements = []
                selectors_to_try = [
                    'div[data-testid="cell-frame-container"]',  # New WhatsApp Web
                    'div[role="listitem"]',  # Older structure
                    '#pane-side div[role="row"]',  # Alternative
                    'div._ak8l',  # Class-based fallback
                ]

                for selector in selectors_to_try:
                    chat_elements = page.query_selector_all(selector)
                    if len(chat_elements) > 0:
                        self.logger.info(f"[OK] Found {len(chat_elements)} chats using selector: {selector}")
                        break
                    else:
                        self.logger.info(f"[DEBUG] Selector '{selector}' found 0 chats, trying next...")

                if len(chat_elements) == 0:
                    self.logger.error("[ERROR] No chats found with any selector!")
                    screenshot_path = self.base_dir / "vault" / f"wa_no_chats_{datetime.now().strftime('%H%M%S')}.png"
                    page.screenshot(path=str(screenshot_path))
                    self.logger.error(f"[ERROR] Screenshot saved: {screenshot_path}")
                    browser.close()
                    return messages_found

                # First pass: collect info about unread chats with keywords
                unread_chats_to_process = []

                for idx, chat_elem in enumerate(chat_elements):
                    try:
                        # Check if chat has unread badge
                        has_unread = False
                        try:
                            unread_selectors = [
                                'span[aria-label*="unread"]',
                                'span[data-testid="icon-unread-count"]',
                                'div[aria-label*="unread"]',
                                'span._akbu',
                            ]
                            for unread_sel in unread_selectors:
                                unread_badge = chat_elem.query_selector(unread_sel)
                                if unread_badge:
                                    has_unread = True
                                    break
                        except:
                            pass

                        if not has_unread:
                            continue

                        # Get chat preview text
                        try:
                            chat_text = chat_elem.inner_text().lower()
                        except:
                            continue

                        # Check if any keyword is in chat text
                        found_keywords = [kw for kw in self.keywords if kw.lower() in chat_text]

                        if found_keywords:
                            unread_chats_to_process.append({
                                'index': idx,
                                'keywords': found_keywords,
                                'preview': chat_text[:100]
                            })
                            self.logger.info(f"[OK] Found unread chat #{idx} with keywords: {found_keywords}")
                    except Exception as e:
                        self.logger.warning(f"[WARN] Error checking chat #{idx}: {e}")
                        continue

                self.logger.info(f"[INFO] Found {len(unread_chats_to_process)} unread chats to process")

                # Second pass: process each unread chat
                processed_chats = []

                for chat_info in unread_chats_to_process:
                    try:
                        # Re-query to get fresh elements
                        for selector in selectors_to_try:
                            fresh_elements = page.query_selector_all(selector)
                            if len(fresh_elements) > 0:
                                break

                        if chat_info['index'] >= len(fresh_elements):
                            self.logger.warning(f"[WARN] Chat index {chat_info['index']} out of range")
                            continue

                        chat_elem = fresh_elements[chat_info['index']]

                        # Click on the chat
                        chat_elem.click()
                        page.wait_for_timeout(3000)

                        # Get sender name from header - try multiple selectors
                        sender = "WhatsApp Contact"
                        try:
                            header_selectors = [
                                'header span[dir="auto"]',
                                'header[data-testid="conversation-header"] span',
                                'div[data-testid="conversation-info-header"] span',
                                'header._amid span',
                            ]
                            for header_sel in header_selectors:
                                header = page.query_selector(header_sel)
                                if header:
                                    sender = header.inner_text().strip()
                                    if sender and len(sender) > 0:
                                        self.logger.info(f"[DEBUG] Sender: {sender} (using {header_sel})")
                                        break
                        except:
                            pass

                        # Skip if already processed this chat
                        if sender in processed_chats:
                            self.logger.info(f"[INFO] Already processed {sender} in this run")
                            continue

                        processed_chats.append(sender)

                        # Get unread messages (messages from other person, not sent by me)
                        message_text = ""
                        try:
                            # Try multiple selectors for incoming messages
                            incoming_msgs = []
                            message_selectors = [
                                'div.message-in span.selectable-text',  # Old structure
                                'div[data-testid="msg-container"] span.selectable-text',  # New structure
                                'div.message-in div.copyable-text span',  # Alternative
                                'div[class*="message-in"] span[dir="ltr"]',  # Broader match
                            ]

                            for msg_sel in message_selectors:
                                incoming_msgs = page.query_selector_all(msg_sel)
                                if len(incoming_msgs) > 0:
                                    self.logger.info(f"[DEBUG] Found {len(incoming_msgs)} incoming messages using: {msg_sel}")
                                    break

                            if incoming_msgs:
                                texts = []
                                for msg in incoming_msgs[-30:]:  # Last 30 messages
                                    try:
                                        t = msg.inner_text().strip()
                                        if t and len(t) > 3:
                                            texts.append(t)
                                    except:
                                        pass
                                message_text = "\n".join(texts)
                                self.logger.info(f"[DEBUG] Extracted {len(texts)} messages")
                            else:
                                self.logger.warning("[WARN] No incoming messages found with any selector")
                        except Exception as e:
                            self.logger.error(f"[ERROR] Message extraction: {e}")

                        # Verify keyword is in extracted messages
                        if message_text and any(kw.lower() in message_text.lower() for kw in chat_info['keywords']):
                            # Use hash for duplicate detection
                            msg_hash = hashlib.md5(message_text.encode()).hexdigest()[:8]
                            msg_id = f"wa_{sender.replace(' ', '_')}_{msg_hash}"

                            if not self.duplicate_tracker.is_duplicate(msg_id):
                                messages_found.append({
                                    'id': msg_id,
                                    'sender': sender,
                                    'text': message_text,
                                    'keywords': chat_info['keywords']
                                })
                                self.duplicate_tracker.mark_processed(msg_id)
                                self.logger.info(f"[OK] Saved message from {sender}")
                            else:
                                self.logger.info(f"[INFO] Already processed: {sender}")
                        else:
                            self.logger.info(f"[WARN] Keywords not found in extracted messages")

                        # Go back to chat list
                        page.goto("https://web.whatsapp.com")
                        page.wait_for_timeout(3000)

                    except Exception as e:
                        self.logger.warning(f"[WARN] Chat processing error: {e}")
                        # Go back to chat list even on error
                        try:
                            page.goto("https://web.whatsapp.com")
                            page.wait_for_timeout(2000)
                        except:
                            pass
                        continue

                self.logger.info(f"[INFO] Found {len(messages_found)} new messages")

                # Keep browser open for 5 seconds before closing
                self.logger.info("[INFO] Keeping browser open for 5 seconds...")
                page.wait_for_timeout(5000)

                browser.close()
                self.logger.info("[INFO] Browser closed")

        except Exception as e:
            self.logger.error(f"[ERROR] {e}")
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

**Keywords:** {', '.join(item['keywords'])}

## Suggested Action
- [ ] Draft a reply
"""
        path.write_text(content, encoding='utf-8')
        return path

if __name__ == "__main__":
    vault_p = project_root / "vault"
    WhatsAppWatcher(str(vault_p)).run()
