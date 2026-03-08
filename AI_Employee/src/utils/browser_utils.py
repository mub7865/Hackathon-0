"""
Browser Utilities for Social Media Automation
Provides stealth mode, session management, and human-like behavior for Playwright
"""

import os
import random
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import logging

logger = logging.getLogger(__name__)


class BrowserManager:
    """
    Manages browser instances with stealth mode and session persistence

    Features:
    - Persistent sessions (cookies, local storage)
    - Stealth mode to avoid detection
    - Human-like delays and mouse movements
    - Automatic retry on failures
    """

    def __init__(
        self,
        session_dir: Optional[str] = None,
        headless: bool = True,
        slow_mo: int = 100
    ):
        """
        Initialize browser manager

        Args:
            session_dir: Directory to store session data (cookies, storage)
            headless: Run browser in headless mode
            slow_mo: Slow down operations by N milliseconds (for human-like behavior)
        """
        self.session_dir = session_dir
        self.headless = headless
        self.slow_mo = slow_mo
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def start(self) -> Page:
        """
        Start browser and return page

        Returns:
            Playwright Page instance
        """
        try:
            # Launch Playwright
            self.playwright = await async_playwright().start()

            # If session_dir provided, use persistent context (same as login script)
            if self.session_dir:
                session_path = Path(self.session_dir)
                session_path.mkdir(parents=True, exist_ok=True)

                # Use persistent context for session persistence
                # IMPORTANT: Keep this EXACTLY the same as login helper scripts
                # Any difference in parameters will make Instagram think it's a different browser
                self.context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir=str(session_path),
                    headless=self.headless,
                    viewport={'width': 1920, 'height': 1080},
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--start-maximized'
                    ]
                )

                # Get or create page
                self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()

            else:
                # No session persistence - use regular browser
                launch_options = {
                    'headless': self.headless,
                    'slow_mo': self.slow_mo,
                    'args': [
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                    ]
                }

                self.browser = await self.playwright.chromium.launch(**launch_options)

                context_options = {
                    'viewport': {'width': 1920, 'height': 1080},
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'locale': 'en-US',
                    'timezone_id': 'America/New_York',
                }

                self.context = await self.browser.new_context(**context_options)
                self.page = await self.context.new_page()

            # Add stealth scripts to context
            await self.context.add_init_script("""
                // Override navigator.webdriver
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });

                // Override plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });

                // Override languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });

                // Override chrome property
                window.chrome = {
                    runtime: {}
                };

                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)

            logger.info("Browser started successfully")
            return self.page

        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            await self.close()
            raise

    async def close(self) -> None:
        """Close browser and cleanup"""
        try:
            # Save session state if session_dir provided
            if self.session_dir and self.context:
                session_path = Path(self.session_dir)
                session_path.mkdir(parents=True, exist_ok=True)
                await self.context.storage_state(path=str(session_path / 'state.json'))
                logger.info(f"Session saved to {session_path}")

            # Close browser
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()

            logger.info("Browser closed successfully")

        except Exception as e:
            logger.error(f"Error closing browser: {e}")

    async def human_delay(self, min_ms: int = 500, max_ms: int = 2000) -> None:
        """
        Add human-like delay

        Args:
            min_ms: Minimum delay in milliseconds
            max_ms: Maximum delay in milliseconds
        """
        delay = random.randint(min_ms, max_ms) / 1000.0
        await asyncio.sleep(delay)

    async def human_type(self, selector: str, text: str, delay_range: tuple = (50, 150)) -> None:
        """
        Type text with human-like delays between keystrokes

        Args:
            selector: CSS selector for input element
            text: Text to type
            delay_range: (min_ms, max_ms) delay between keystrokes
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        element = await self.page.wait_for_selector(selector)

        for char in text:
            await element.type(char)
            delay = random.randint(delay_range[0], delay_range[1]) / 1000.0
            await asyncio.sleep(delay)

    async def human_click(self, selector: str, delay_before: tuple = (500, 1500)) -> None:
        """
        Click element with human-like delay before clicking

        Args:
            selector: CSS selector for element
            delay_before: (min_ms, max_ms) delay before clicking
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        # Wait for element
        await self.page.wait_for_selector(selector)

        # Human delay before clicking
        await self.human_delay(delay_before[0], delay_before[1])

        # Click
        await self.page.click(selector)

    async def scroll_slowly(self, distance: int = 300, steps: int = 5) -> None:
        """
        Scroll page slowly in steps (human-like)

        Args:
            distance: Total scroll distance in pixels
            steps: Number of scroll steps
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        step_distance = distance // steps

        for _ in range(steps):
            await self.page.evaluate(f"window.scrollBy(0, {step_distance})")
            await self.human_delay(100, 300)

    async def wait_for_navigation(self, timeout: int = 30000) -> None:
        """
        Wait for page navigation to complete

        Args:
            timeout: Timeout in milliseconds
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        await self.page.wait_for_load_state('networkidle', timeout=timeout)

    async def take_screenshot(self, path: str) -> None:
        """
        Take screenshot of current page

        Args:
            path: Path to save screenshot
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        await self.page.screenshot(path=path)
        logger.info(f"Screenshot saved to {path}")

    async def is_logged_in(self, check_selector: str) -> bool:
        """
        Check if user is logged in by looking for a specific element

        Args:
            check_selector: CSS selector that only appears when logged in

        Returns:
            True if logged in, False otherwise
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        try:
            await self.page.wait_for_selector(check_selector, timeout=5000)
            return True
        except:
            return False

    async def get_cookies(self) -> list:
        """
        Get all cookies from current context

        Returns:
            List of cookie dictionaries
        """
        if not self.context:
            raise RuntimeError("Browser not started")

        return await self.context.cookies()

    async def set_cookies(self, cookies: list) -> None:
        """
        Set cookies in current context

        Args:
            cookies: List of cookie dictionaries
        """
        if not self.context:
            raise RuntimeError("Browser not started")

        await self.context.add_cookies(cookies)


class FacebookBrowser(BrowserManager):
    """Browser manager specifically for Facebook automation"""

    def __init__(self, session_dir: Optional[str] = None, headless: bool = True):
        """
        Initialize Facebook browser

        Args:
            session_dir: Directory to store Facebook session
            headless: Run browser in headless mode
        """
        if session_dir is None:
            session_dir = os.getenv('FACEBOOK_SESSION', './sessions/facebook')

        super().__init__(session_dir=session_dir, headless=headless, slow_mo=100)

    async def navigate_to_facebook(self) -> None:
        """Navigate to Facebook homepage"""
        if not self.page:
            raise RuntimeError("Browser not started")

        # Use domcontentloaded instead of networkidle (faster, more reliable)
        await self.page.goto('https://www.facebook.com', wait_until='domcontentloaded', timeout=60000)
        await self.human_delay(1000, 2000)

    async def is_logged_in_facebook(self) -> bool:
        """Check if logged into Facebook"""
        return await self.is_logged_in('[aria-label="Create a post"]')


class InstagramBrowser(BrowserManager):
    """Browser manager specifically for Instagram automation"""

    def __init__(self, session_dir: Optional[str] = None, headless: bool = True):
        """
        Initialize Instagram browser

        Args:
            session_dir: Directory to store Instagram session
            headless: Run browser in headless mode
        """
        if session_dir is None:
            session_dir = os.getenv('INSTAGRAM_SESSION', './sessions/instagram')

        super().__init__(session_dir=session_dir, headless=headless, slow_mo=100)

    async def navigate_to_instagram(self) -> None:
        """Navigate to Instagram homepage"""
        if not self.page:
            raise RuntimeError("Browser not started")

        # Use domcontentloaded instead of networkidle (faster, more reliable)
        await self.page.goto('https://www.instagram.com', wait_until='domcontentloaded', timeout=60000)
        await self.human_delay(1000, 2000)

    async def is_logged_in_instagram(self) -> bool:
        """Check if logged into Instagram"""
        return await self.is_logged_in('[aria-label="New post"]')


# Utility functions

async def create_facebook_browser(headless: bool = True) -> FacebookBrowser:
    """
    Create and start Facebook browser

    Args:
        headless: Run browser in headless mode

    Returns:
        Started FacebookBrowser instance
    """
    browser = FacebookBrowser(headless=headless)
    await browser.start()
    return browser


async def create_instagram_browser(headless: bool = True) -> InstagramBrowser:
    """
    Create and start Instagram browser

    Args:
        headless: Run browser in headless mode

    Returns:
        Started InstagramBrowser instance
    """
    browser = InstagramBrowser(headless=headless)
    await browser.start()
    return browser
