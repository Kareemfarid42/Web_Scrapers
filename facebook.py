"""
Facebook Email Scraper for Yellow Pages Business Listings
Senior Python Automation Engineer Implementation

This script takes the output from the Yellow Pages scraper (Excel file with
Business Name and Phone Number) and extracts email addresses from their
Facebook pages using Google search.

Required packages:
    pip install selenium webdriver-manager openpyxl pandas undetected-chromedriver
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import time
import random
import re
from pathlib import Path


class FacebookEmailScraper:
    """Scraper class to extract email addresses from Facebook business pages."""
    
    def __init__(self):
        """Initialize the scraper with Undetected Chrome WebDriver."""
        print("Initializing Undetected Chrome WebDriver...")
        
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--start-maximized')
        
        self.driver = uc.Chrome(options=options, version_main=144)
        self.wait = WebDriverWait(self.driver, 20)
        
        print("WebDriver initialized successfully.\n")
    
    def search_google(self, business_name):
        """
        Search Google for the business's Facebook page.
        
        Args:
            business_name (str): The name of the business
            
        Returns:
            str: URL of the Facebook page, or None if not found
        """
        search_query = f'"{business_name}" facebook'
        
        try:
            self.driver.get("https://www.google.com/search")
            time.sleep(random.uniform(2, 4))
            
            # Find the Google search input field
            search_input = None
            search_selectors = [
                (By.NAME, "q"),
                (By.ID, "APjFqb"),
                (By.CSS_SELECTOR, "input[type='text']")
            ]
            
            for by, selector in search_selectors:
                try:
                    search_input = self.wait.until(EC.element_to_be_clickable((by, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not search_input:
                print(f"  ⚠️  Could not find Google search input. Skipping...")
                return None
            
            # Enter search query
            search_input.click()
            search_input.clear()
            time.sleep(0.3)
            search_input.send_keys(search_query)
            time.sleep(1)
            
            # Submit search
            search_input.submit()
            time.sleep(3)
            
            # Look for Facebook results
            try:
                # Wait for results to appear
                self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='facebook.com']")))
                
                # Find Facebook links in search results
                facebook_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='facebook.com']")
                
                for link in facebook_links:
                    href = link.get_attribute('href')
                    
                    # Filter for business pages (not posts, comments, etc.)
                    if href and 'facebook.com' in href:
                        # Skip if it's a share or interaction link
                        if any(x in href for x in ['share', 'comment', 'like', 'watch', 'video']):
                            continue
                        
                        # Extract the main Facebook URL
                        if 'facebook.com/' in href:
                            # Remove query parameters and tracking
                            facebook_url = href.split('&')[0].split('?')[0]
                            
                            # Validate it's a page URL
                            if 'facebook.com/pages' in facebook_url or 'facebook.com/pg' in facebook_url:
                                return facebook_url
                            # Also accept direct page URLs like facebook.com/business
                            elif facebook_url.count('/') >= 3:
                                return facebook_url
                
                # If no specific page URL found, return the first Facebook link
                if facebook_links:
                    href = facebook_links[0].get_attribute('href')
                    if href:
                        return href.split('&')[0].split('?')[0]
                
            except TimeoutException:
                pass
            
            return None
            
        except Exception as e:
            print(f"  ⚠️  Error searching Google: {str(e)}")
            return None
    
    def extract_email_from_facebook(self, facebook_url):
        """
        Extract email from a Facebook business page's intro section.
        
        Args:
            facebook_url (str): URL of the Facebook page
            
        Returns:
            str: Email address found, or "NaN" if not found
        """
        try:
            # Normalize Facebook URL
            if not facebook_url.startswith('http'):
                facebook_url = 'https://' + facebook_url
            
            self.driver.get(facebook_url)
            time.sleep(3)
            
            # Try multiple selectors to find email in the intro section
            email_selectors = [
                (By.XPATH, "//*[contains(text(), '@')]"),  # Any text containing @
                (By.CSS_SELECTOR, "span[data-field='email']"),
                (By.CSS_SELECTOR, "[data-field='email']"),
                (By.XPATH, "//span[contains(., '@')]"),
                (By.CSS_SELECTOR, "div[role='main'] a[href*='mailto:']"),
                (By.XPATH, "//a[contains(@href, 'mailto:')]"),
            ]
            
            for by, selector in email_selectors:
                try:
                    elements = self.driver.find_elements(by, selector)
                    for element in elements:
                        text = element.text.strip()
                        
                        # Check if it looks like an email
                        if '@' in text:
                            email = self._extract_email_regex(text)
                            if email:
                                return email
                        
                        # Check href for mailto links
                        href = element.get_attribute('href') or ''
                        if 'mailto:' in href:
                            email = href.replace('mailto:', '').split('?')[0].strip()
                            if email and '@' in email:
                                return email
                except:
                    continue
            
            # Method: Parse page HTML with regex for email patterns
            page_html = self.driver.page_source
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', page_html)
            
            if emails:
                # Filter out common non-contact emails
                valid_emails = [e for e in emails if not any(x in e for x in [
                    'facebook.com', 'support@', 'noreply', 'no-reply', 'notification'
                ])]
                
                if valid_emails:
                    return valid_emails[0]
            
            return "NaN"
            
        except Exception as e:
            print(f"  ⚠️  Error extracting email from Facebook: {str(e)}")
            return "NaN"
    
    def _extract_email_regex(self, text):
        """Extract email from text using regex."""
        match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        return match.group(0) if match else None
    
    def close(self):
        """Close the browser."""
        print("\nClosing browser...")
        self.driver.quit()
        print("Browser closed.\n")


def process_excel_file(excel_path):
    """
    Process the Yellow Pages Excel file and add Facebook email column.
    
    Args:
        excel_path (str): Path to the Yellow Pages Excel file
    """
    # Verify file exists
    if not Path(excel_path).exists():
        print(f"ERROR: File not found: {excel_path}")
        return
    
    print(f"Loading Excel file: {excel_path}")
    
    # Read the Excel file
    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        print(f"ERROR reading Excel file: {str(e)}")
        return
    
    print(f"Successfully loaded {len(df)} business listings.\n")
    
    # Check if required columns exist
    if 'Business Name' not in df.columns:
        print("ERROR: 'Business Name' column not found in Excel file.")
        return
    
    # Add Email column if it doesn't exist
    if 'Email' not in df.columns:
        df['Email'] = "NaN"
    
    print("="*80)
    print("STARTING FACEBOOK EMAIL EXTRACTION")
    print("="*80)
    print("This may take several minutes depending on the number of listings...")
    print("Progress will be shown after each 5 listings.\n")
    
    # Initialize scraper
    scraper = FacebookEmailScraper()
    
    try:
        for idx, row in df.iterrows():
            business_name = row['Business Name']
            
            # Skip if email already found
            if pd.notna(row['Email']) and row['Email'] != "NaN":
                print(f"Listing {idx + 1}/{len(df)}: {business_name} - Already has email, skipping")
                continue
            
            print(f"\nListing {idx + 1}/{len(df)}: {business_name}")
            print(f"  Searching Google for Facebook page...")
            
            # Apply delay between searches
            time.sleep(random.uniform(3, 6))
            
            # Search for Facebook page
            facebook_url = scraper.search_google(business_name)
            
            if not facebook_url:
                print(f"  ❌ Facebook page not found")
                df.at[idx, 'Email'] = "NaN"
            else:
                print(f"  ✓ Found Facebook page: {facebook_url[:60]}...")
                print(f"  Extracting email from intro section...")
                
                # Apply delay before accessing Facebook
                time.sleep(random.uniform(2, 4))
                
                # Extract email
                email = scraper.extract_email_from_facebook(facebook_url)
                
                if email != "NaN":
                    print(f"  ✓ Email found: {email}")
                    df.at[idx, 'Email'] = email
                else:
                    print(f"  ❌ Email not found in intro section")
                    df.at[idx, 'Email'] = "NaN"
            
            # Auto-save every 10 listings
            if (idx + 1) % 10 == 0:
                print(f"\n💾 Auto-saving progress ({idx + 1}/{len(df)} listings processed)...")
                try:
                    df.to_excel(excel_path, index=False, sheet_name='Results')
                    print(f"  ✓ Saved successfully\n")
                except Exception as e:
                    print(f"  ⚠️  Error saving: {str(e)}\n")
        
        # Final save
        print(f"\n💾 Saving final results...")
        df.to_excel(excel_path, index=False, sheet_name='Results')
        
        print(f"\n{'='*80}")
        print("EXTRACTION COMPLETE")
        print(f"{'='*80}")
        print(f"Successfully processed {len(df)} listings")
        
        # Count results
        with_email = sum(1 for e in df['Email'] if pd.notna(e) and e != "NaN")
        without_email = len(df) - with_email
        
        print(f"  - With Email: {with_email}")
        print(f"  - Without Email: {without_email}")
        print(f"{'='*80}\n")
        
        # Show preview
        print("PREVIEW (First 5 Results):")
        print("-"*80)
        for idx, row in df.head().iterrows():
            name = row['Business Name'][:40]
            email = row['Email']
            print(f"{idx + 1}. {name:<40} | {email}")
        
        if len(df) > 10:
            print(f"\n... ({len(df) - 10} more) ...\n")
            print("PREVIEW (Last 5 Results):")
            print("-"*80)
            for idx, row in df.tail().iterrows():
                name = row['Business Name'][:40]
                email = row['Email']
                print(f"{idx + 1}. {name:<40} | {email}")
        
        print(f"{'='*80}\n")
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  INTERRUPTED BY USER (Ctrl+C)")
        print(f"Saving {len(df)} listings processed so far...\n")
        try:
            df.to_excel(excel_path, index=False, sheet_name='Results')
            print("✓ Data saved successfully\n")
        except Exception as e:
            print(f"ERROR saving: {str(e)}\n")
    
    finally:
        scraper.close()


def main():
    """Main execution function."""
    print("="*80)
    print("FACEBOOK EMAIL SCRAPER FOR YELLOW PAGES LISTINGS")
    print("="*80)
    print()
    
    # Get Excel file path from user
    excel_path = input("Enter the path to your Yellow Pages Excel file (e.g., YellowPages_Plumber_LosAngelesCA.xlsx): ").strip()
    
    if not excel_path:
        print("\nERROR: Excel file path is required.")
        return
    
    print()
    process_excel_file(excel_path)
    print("\nScript execution completed.")


if __name__ == "__main__":
    main()