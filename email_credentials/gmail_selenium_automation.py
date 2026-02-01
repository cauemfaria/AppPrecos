"""
Gmail Aliases Bulk Automation using Selenium - Simplified Version
Automatically adds email aliases to your Gmail account
"""

import csv
import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import os

class GmailAliasAdder:
    def __init__(self, email, password, csv_file="credentials.csv", headless=False):
        self.email = email
        self.password = password
        self.csv_file = csv_file
        self.driver = None
        self.wait = None
        self.headless = headless
        self.aliases_added = 0
        self.aliases_failed = []
    
    def setup_driver(self):
        """Initialize Chrome WebDriver."""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--user-data-dir=/tmp/chrome_profile")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            if self.headless:
                options.add_argument("--headless")
            
            # Use webdriver-manager to auto-download ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(30)
            self.wait = WebDriverWait(self.driver, 15)
            print("[OK] Chrome WebDriver initialized")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to initialize WebDriver: {e}")
            return False
    
    def login_gmail(self):
        """Log into Gmail account."""
        try:
            print("\n[STEP 1] Logging into Gmail...")
            self.driver.get("https://accounts.google.com/ServiceLogin")
            print("  - Page loaded, waiting for email field...")
            time.sleep(3)
            
            # Enter email
            try:
                email_field = self.wait.until(EC.presence_of_element_located((By.ID, "identifierId")))
                email_field.send_keys(self.email)
                print("  - Email entered")
            except Exception as e:
                print(f"  - Error entering email: {e}")
                return False
            
            try:
                next_button = self.driver.find_element(By.ID, "identifierNext")
                next_button.click()
                print("  - Clicked Next")
                time.sleep(3)
            except Exception as e:
                print(f"  - Error clicking Next: {e}")
                return False
            
            # Enter password
            try:
                password_field = self.wait.until(EC.presence_of_element_located((By.NAME, "password")))
                password_field.send_keys(self.password)
                print("  - Password entered")
            except Exception as e:
                print(f"  - Error entering password: {e}")
                print("  - Note: If you have 2FA enabled, you'll need to manually verify")
                return False
            
            try:
                next_button = self.driver.find_element(By.ID, "passwordNext")
                next_button.click()
                print("  - Clicked Password Next")
                time.sleep(5)
            except Exception as e:
                print(f"  - Error clicking Password Next: {e}")
                return False
            
            # Verify we're logged in
            current_url = self.driver.current_url
            print(f"  - Current URL: {current_url}")
            
            if "accounts.google.com" not in current_url and "mail" not in current_url:
                print("[ERROR] Unexpected redirect")
                return False
            
            print("[OK] Login completed (manual verification may be needed)")
            return True
        except Exception as e:
            print(f"[ERROR] Login failed: {e}")
            return False
    
    def navigate_to_settings(self):
        """Navigate to Gmail settings."""
        try:
            print("\n[STEP 2] Navigating to Gmail settings...")
            self.driver.get("https://mail.google.com/mail/u/0/#settings/accounts")
            time.sleep(4)
            print("[OK] Navigated to settings page")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to navigate: {e}")
            return False
    
    def read_aliases_from_csv(self, limit=None):
        """Read email aliases from CSV file."""
        aliases = []
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for idx, row in enumerate(reader):
                    if limit and idx >= limit:
                        break
                    email = row.get('Email', '').strip()
                    if email:
                        aliases.append(email)
            
            print(f"[OK] Loaded {len(aliases)} aliases from CSV")
            return aliases
        except Exception as e:
            print(f"[ERROR] Failed to read CSV: {e}")
            return []
    
    def add_alias(self, alias_email):
        """Add a single email alias."""
        try:
            print(f"  - {self.aliases_added + len(self.aliases_failed) + 1}. Adding {alias_email}...", end=" ", flush=True)
            time.sleep(1)
            
            # Take screenshot for debugging
            # self.driver.save_screenshot(f"debug_{self.aliases_added}.png")
            
            # Try to find and click the add button
            try:
                add_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Add another email')]"))
                )
                add_button.click()
                print("(clicked button)", end=" ", flush=True)
            except:
                print("(button not found)", end=" ", flush=True)
                self.aliases_failed.append(alias_email)
                return False
            
            time.sleep(2)
            
            # Enter email in popup
            try:
                email_input = self.wait.until(EC.presence_of_element_located((By.ID, "add-email")))
                email_input.send_keys(alias_email)
                print("(email entered)", end=" ", flush=True)
            except:
                print("(no email field)", end=" ", flush=True)
                self.aliases_failed.append(alias_email)
                return False
            
            # Click Next
            try:
                next_button = self.driver.find_element(By.XPATH, "//button[contains(., 'Next')]")
                next_button.click()
                print("(next clicked)", end=" ", flush=True)
                time.sleep(2)
            except:
                print("(no next button)", end=" ", flush=True)
                self.aliases_failed.append(alias_email)
                return False
            
            print("SUCCESS")
            self.aliases_added += 1
            return True
        
        except Exception as e:
            print(f"FAILED: {str(e)[:50]}")
            self.aliases_failed.append(alias_email)
            return False
    
    def run_batch(self, limit=3):
        """Run the automation for batch of aliases."""
        try:
            # Setup
            if not self.setup_driver():
                return False
            
            time.sleep(2)
            
            # Login
            if not self.login_gmail():
                print("\n[WARNING] Login incomplete. Continuing to settings page...")
                # Try to navigate anyway
                time.sleep(3)
            
            # Navigate
            if not self.navigate_to_settings():
                return False
            
            # Read aliases
            aliases = self.read_aliases_from_csv(limit=limit)
            if not aliases:
                return False
            
            # Add each alias
            print(f"\n[STEP 3] Adding {len(aliases)} aliases...\n")
            for alias in aliases:
                self.add_alias(alias)
                time.sleep(2)
            
            # Summary
            print("\n" + "="*70)
            print(f"[SUMMARY] Successfully added: {self.aliases_added}/{len(aliases)}")
            if self.aliases_failed:
                print(f"Failed: {len(self.aliases_failed)}")
            print("="*70)
            
            return self.aliases_added > 0
        
        except Exception as e:
            print(f"[ERROR] Batch run failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            if self.driver:
                print("\n[Closing browser in 5 seconds...]")
                time.sleep(5)
                self.driver.quit()

def main():
    print("="*70)
    print("Gmail Aliases Bulk Automation Tool - Selenium Edition")
    print("="*70)
    
    # Get credentials from environment
    email = os.getenv('GMAIL_EMAIL')
    password = os.getenv('GMAIL_PASSWORD')
    
    if not email or not password:
        print("\n[ERROR] Missing credentials!")
        print("\nUsage:")
        print("  set GMAIL_EMAIL=your_email@gmail.com")
        print("  set GMAIL_PASSWORD=your_password")
        print("  python gmail_selenium_automation.py")
        return
    
    print(f"\n[INFO] Gmail: {email}")
    print("[INFO] Password: (hidden)")
    
    # Test with 3 aliases first
    print("\n" + "-"*70)
    print("STEP 0: Testing with 3 aliases")
    print("-"*70)
    
    adder = GmailAliasAdder(email, password, headless=False)
    success = adder.run_batch(limit=3)
    
    if success:
        print("\n[SUCCESS] Test batch completed!")
        print("\nTo run the FULL batch (100 aliases), modify the script:")
        print("  Change: adder.run_batch(limit=3)")
        print("  To:     adder.run_batch(limit=None)")
    else:
        print("\n[FAILED] Test batch had issues. Check the output above.")
        print("\nCommon issues:")
        print("  1. 2FA enabled on account - manually verify when prompted")
        print("  2. Chrome WebDriver version mismatch - try: pip install --upgrade webdriver-manager")
        print("  3. Network connectivity - check your internet connection")

if __name__ == "__main__":
    main()
