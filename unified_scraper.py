"""
UNIFIED WEB SCRAPER - Yellow Pages + Facebook Email
Senior Python Automation Engineer Implementation

This script combines both scrapers into one workflow:
1. First: Scrapes business listings from yellowpages.com
2. Saves results to Excel file
3. Then: Automatically extracts email addresses from Facebook business pages
4. Updates same Excel file with Email column

This means you only need to run ONE script!

Required packages:
    pip install selenium webdriver-manager openpyxl pandas undetected-chromedriver
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import pandas as pd
import re
import random
from pathlib import Path


# ============================================================================
# PART 1: YELLOW PAGES SCRAPER
# ============================================================================

class YellowPagesScraper:
    """Scraper class for Yellow Pages (yellowpages.com) website."""
    
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
    
    def navigate_to_site(self):
        """Navigate to Yellow Pages homepage."""
        print("Navigating to https://www.yellowpages.com/...")
        self.driver.get("https://www.yellowpages.com/")
        
        sleep_time = random.uniform(2, 5)
        time.sleep(sleep_time)
        print(f"Page loaded (waited {sleep_time:.2f}s).\n")
    
    def perform_search(self, job_type, location):
        """Perform search on Yellow Pages."""
        print(f"Searching for: '{job_type}' in '{location}'...")
        
        try:
            time.sleep(random.uniform(2, 4))
            
            # Find the "What" input field
            what_field = None
            what_selectors = [
                (By.ID, "query"),
                (By.NAME, "search_terms"),
                (By.CSS_SELECTOR, "input.search-input"),
                (By.CSS_SELECTOR, "#search-form input[type='text']")
            ]
            
            for by, selector in what_selectors:
                try:
                    what_field = self.wait.until(EC.element_to_be_clickable((by, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not what_field:
                raise Exception("Could not find 'What' input field")
            
            what_field.click()
            what_field.clear()
            time.sleep(0.5)
            what_field.send_keys(job_type)
            print(f"✓ Entered '{job_type}' in 'What' field.")
            
            # Find the "Where" input field
            where_field = None
            where_selectors = [
                (By.ID, "location"),
                (By.CSS_SELECTOR, "input[placeholder*='Where']"),
                (By.CSS_SELECTOR, "input#geo_location_terms"),
                (By.NAME, "geo_location_terms"),
                (By.CSS_SELECTOR, "#search-form input[placeholder*='Where']")
            ]
            
            for by, selector in where_selectors:
                try:
                    where_field = self.wait.until(EC.element_to_be_clickable((by, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not where_field:
                raise Exception("Could not find 'Where' input field")
            
            where_field.click()
            where_field.clear()
            time.sleep(0.5)
            where_field.send_keys(location)
            print(f"✓ Entered '{location}' in 'Where' field.")
            
            # Find and click search button
            time.sleep(1)
            search_button = None
            button_selectors = [
                (By.CSS_SELECTOR, "button[value='Find']"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.CSS_SELECTOR, ".search-submit"),
                (By.XPATH, "//button[contains(text(), 'FIND')]"),
                (By.XPATH, "//button[@type='submit']")
            ]
            
            for by, selector in button_selectors:
                try:
                    search_button = self.driver.find_element(by, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if search_button:
                self.driver.execute_script("arguments[0].click();", search_button)
                print("✓ Search button clicked.\n")
            else:
                where_field.send_keys(Keys.RETURN)
                print("✓ Submitted search via Enter key.\n")
            
            time.sleep(4)
            print(f"Navigated to: {self.driver.current_url}\n")
            
            self.wait.until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, 
                    ".result, .search-results, .organic, [class*='result']"
                ))
            )
            print("Search results loaded successfully.\n")
            
        except TimeoutException as e:
            print(f"ERROR: Timeout while performing search.")
            raise
        except Exception as e:
            print(f"ERROR: {str(e)}")
            raise
    
    def extract_listings(self, job_type="", location=""):
        """Extract business listings from search results across multiple pages."""
        print(f"Extracting ALL listings from all pages...\n")
        
        results = []
        current_page = 1
        
        try:
            while True:
                print(f"{'='*60}")
                print(f"SCRAPING PAGE {current_page}")
                print(f"{'='*60}\n")
                
                listing_selectors = [
                    ".srp-listing",
                    ".result",
                    ".search-results .result",
                    ".organic",
                    "[class*='srp-listing']",
                    "[class*='result-item']"
                ]
                
                listings = []
                for selector in listing_selectors:
                    try:
                        listings = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if listings:
                            print(f"Found {len(listings)} listings on page {current_page}\n")
                            break
                    except:
                        continue
                
                if not listings:
                    print(f"No listings found on page {current_page}. Stopping.")
                    break
                
                for idx, listing in enumerate(listings, 1):
                    print(f"Processing listing #{len(results) + 1} (Page {current_page}, Item {idx})...")
                    
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", listing)
                        time.sleep(0.5)
                        
                        # Extract business name
                        business_name = "Unknown"
                        name_selectors = [
                            "a.business-name",
                            ".business-name",
                            "h2.n a",
                            ".info-section h2 a",
                            "[class*='business-name']",
                            ".info h2 a"
                        ]
                        
                        for name_sel in name_selectors:
                            try:
                                name_element = listing.find_element(By.CSS_SELECTOR, name_sel)
                                business_name = name_element.text.strip()
                                if business_name:
                                    break
                            except NoSuchElementException:
                                continue
                        
                        if business_name == "Unknown":
                            print("  Warning: Business name not found. Skipping this listing.")
                            continue
                        
                        # Extract phone number
                        phone_number = "Not Available"
                        phone_found = False
                        
                        phone_selectors = [
                            ".phones.phone.primary",
                            ".phone.primary",
                            ".phones",
                            "div.phone",
                            "[class*='phone primary']",
                            ".info-secondary .phone"
                        ]
                        
                        for phone_sel in phone_selectors:
                            try:
                                phone_elements = listing.find_elements(By.CSS_SELECTOR, phone_sel)
                                for phone_el in phone_elements:
                                    phone_text = phone_el.text.strip()
                                    phone_text = ' '.join(phone_text.split())
                                    
                                    if phone_text and (phone_text[0].isdigit() or phone_text.startswith('(')):
                                        phone_number = phone_text
                                        phone_found = True
                                        break
                            except:
                                continue
                            
                            if phone_found:
                                break
                        
                        if not phone_found:
                            try:
                                phone_links = listing.find_elements(By.CSS_SELECTOR, "a[href^='tel:']")
                                for phone_link in phone_links:
                                    phone_text = phone_link.text.strip()
                                    if not phone_text:
                                        href = phone_link.get_attribute('href')
                                        phone_text = href.replace('tel:', '').replace('+1', '').strip()
                                    
                                    if phone_text and len(phone_text) >= 10:
                                        phone_number = phone_text
                                        phone_found = True
                                        break
                            except:
                                pass
                        
                        if not phone_found:
                            try:
                                listing_html = listing.get_attribute('innerHTML')
                                phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
                                matches = re.findall(phone_pattern, listing_html)
                                if matches:
                                    phone_number = matches[0]
                            except:
                                pass
                        
                        if business_name != "Unknown":
                            results.append({
                                "Business Name": business_name,
                                "Phone Number": phone_number
                            })
                        
                    except Exception as e:
                        continue
                
                # Try to navigate to next page
                print(f"\nLooking for 'Next' button to go to page {current_page + 1}...\n")
                
                next_button_found = False
                next_button_selectors = [
                    "a.next",
                    "a[rel='next']",
                    ".pagination a.next",
                    "a[aria-label='Next']",
                    ".next a"
                ]
                
                for next_sel in next_button_selectors:
                    try:
                        next_buttons = self.driver.find_elements(By.CSS_SELECTOR, next_sel)
                        
                        for next_button in next_buttons:
                            button_class = next_button.get_attribute('class') or ''
                            
                            if 'disabled' in button_class.lower():
                                print("Next button is disabled. Reached last page.\n")
                                break
                            
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                            time.sleep(1)
                            
                            old_url = self.driver.current_url
                            self.driver.execute_script("arguments[0].click();", next_button)
                            
                            time.sleep(3)
                            new_url = self.driver.current_url
                            
                            if new_url != old_url:
                                print(f"✓ Successfully navigated to page {current_page + 1}")
                                next_button_found = True
                                current_page += 1
                                time.sleep(2)
                                break
                        
                        if next_button_found:
                            break
                            
                    except Exception as e:
                        continue
                
                if not next_button_found:
                    print("No 'Next' button found or last page reached. Stopping pagination.\n")
                    break
            
            print(f"{'='*60}")
            print(f"Yellow Pages extraction complete. Successfully scraped {len(results)} listings.")
            print(f"{'='*60}\n")
            return results
            
        except KeyboardInterrupt:
            print(f"\n\n⚠️  INTERRUPTED BY USER")
            return results
        except Exception as e:
            print(f"ERROR during extraction: {str(e)}")
            return results
    
    def close(self):
        """Close the browser and clean up."""
        print("Closing Yellow Pages browser...")
        self.driver.quit()
        print("Browser closed.\n")


# ============================================================================
# PART 2: FACEBOOK EMAIL SCRAPER
# ============================================================================

class FacebookEmailScraper:
    """Scraper class to extract email addresses from Facebook business pages."""
    
    def __init__(self):
        """Initialize the scraper with Undetected Chrome WebDriver."""
        print("Initializing Chrome WebDriver for Facebook scraping...")
        
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--start-maximized')
        
        self.driver = uc.Chrome(options=options, version_main=144)
        self.wait = WebDriverWait(self.driver, 20)
        
        print("WebDriver initialized successfully.\n")
    
    def search_google(self, business_name):
        """Search Google for the business's Facebook page."""
        search_query = f'"{business_name}" facebook'
        
        try:
            self.driver.get("https://www.google.com/search")
            time.sleep(random.uniform(2, 4))
            
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
                return None
            
            search_input.click()
            search_input.clear()
            time.sleep(0.3)
            search_input.send_keys(search_query)
            time.sleep(1)
            
            search_input.submit()
            time.sleep(3)
            
            try:
                self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='facebook.com']")))
                facebook_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='facebook.com']")
                
                for link in facebook_links:
                    href = link.get_attribute('href')
                    
                    if href and 'facebook.com' in href:
                        if any(x in href for x in ['share', 'comment', 'like', 'watch', 'video']):
                            continue
                        
                        if 'facebook.com/' in href:
                            facebook_url = href.split('&')[0].split('?')[0]
                            
                            if 'facebook.com/pages' in facebook_url or 'facebook.com/pg' in facebook_url:
                                return facebook_url
                            elif facebook_url.count('/') >= 3:
                                return facebook_url
                
                if facebook_links:
                    href = facebook_links[0].get_attribute('href')
                    if href:
                        return href.split('&')[0].split('?')[0]
                
            except TimeoutException:
                pass
            
            return None
            
        except Exception as e:
            return None
    
    def extract_email_from_facebook(self, facebook_url):
        """Extract email from a Facebook business page's intro section."""
        try:
            if not facebook_url.startswith('http'):
                facebook_url = 'https://' + facebook_url
            
            self.driver.get(facebook_url)
            time.sleep(3)
            
            email_selectors = [
                (By.XPATH, "//*[contains(text(), '@')]"),
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
                        
                        if '@' in text:
                            email = self._extract_email_regex(text)
                            if email:
                                return email
                        
                        href = element.get_attribute('href') or ''
                        if 'mailto:' in href:
                            email = href.replace('mailto:', '').split('?')[0].strip()
                            if email and '@' in email:
                                return email
                except:
                    continue
            
            page_html = self.driver.page_source
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', page_html)
            
            if emails:
                valid_emails = [e for e in emails if not any(x in e for x in [
                    'facebook.com', 'support@', 'noreply', 'no-reply', 'notification'
                ])]
                
                if valid_emails:
                    return valid_emails[0]
            
            return "NaN"
            
        except Exception as e:
            return "NaN"
    
    def _extract_email_regex(self, text):
        """Extract email from text using regex."""
        match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        return match.group(0) if match else None
    
    def close(self):
        """Close the browser."""
        print("Closing Facebook scraper browser...")
        self.driver.quit()
        print("Browser closed.\n")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def save_to_excel(results, job_type, location):
    """Save scraper results to Excel file."""
    if not results:
        print("No results to save.")
        return None
    
    df = pd.DataFrame(results)
    filename = f"YellowPages_{job_type}_{location}.xlsx"
    filename = "".join(c for c in filename if c.isalnum() or c in ('_', '.', '-'))
    
    try:
        df.to_excel(filename, index=False, sheet_name='Results')
        print(f"\n{'='*80}")
        print(f"✓ SUCCESS! Data saved to Excel file: {filename}")
        print(f"{'='*80}")
        print(f"Total records saved: {len(results)}")
        print(f"Columns: {', '.join(df.columns.tolist())}")
        print(f"{'='*80}\n")
        return filename
        
    except Exception as e:
        print(f"\nERROR saving to Excel: {str(e)}\n")
        return None


def process_excel_for_emails(excel_path):
    """Process the Yellow Pages Excel file and add Facebook email column."""
    if not Path(excel_path).exists():
        print(f"ERROR: File not found: {excel_path}")
        return False
    
    print(f"\n\nLoading Excel file for Facebook email extraction: {excel_path}")
    
    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        print(f"ERROR reading Excel file: {str(e)}")
        return False
    
    print(f"Successfully loaded {len(df)} business listings.\n")
    
    if 'Business Name' not in df.columns:
        print("ERROR: 'Business Name' column not found in Excel file.")
        return False
    
    if 'Email' not in df.columns:
        df['Email'] = "NaN"
    
    print("="*80)
    print("STARTING FACEBOOK EMAIL EXTRACTION")
    print("="*80)
    print("This may take several minutes depending on the number of listings...")
    print("Progress will be shown after each listing.\n")
    
    scraper = FacebookEmailScraper()
    
    try:
        for idx, row in df.iterrows():
            business_name = row['Business Name']
            
            if pd.notna(row['Email']) and row['Email'] != "NaN":
                print(f"Listing {idx + 1}/{len(df)}: {business_name} - Already has email, skipping")
                continue
            
            print(f"\nListing {idx + 1}/{len(df)}: {business_name}")
            print(f"  Searching Google for Facebook page...")
            
            time.sleep(random.uniform(3, 6))
            
            facebook_url = scraper.search_google(business_name)
            
            if not facebook_url:
                print(f"  ❌ Facebook page not found")
                df.at[idx, 'Email'] = "NaN"
            else:
                print(f"  ✓ Found Facebook page: {facebook_url[:60]}...")
                print(f"  Extracting email from intro section...")
                
                time.sleep(random.uniform(2, 4))
                
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
        print("FACEBOOK EMAIL EXTRACTION COMPLETE")
        print(f"{'='*80}")
        print(f"Successfully processed {len(df)} listings")
        
        with_email = sum(1 for e in df['Email'] if pd.notna(e) and e != "NaN")
        without_email = len(df) - with_email
        
        print(f"  - With Email: {with_email}")
        print(f"  - Without Email: {without_email}")
        print(f"{'='*80}\n")
        
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
        
        return True
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  INTERRUPTED BY USER (Ctrl+C)")
        print(f"Saving {len(df)} listings processed so far...\n")
        try:
            df.to_excel(excel_path, index=False, sheet_name='Results')
            print("✓ Data saved successfully\n")
        except Exception as e:
            print(f"ERROR saving: {str(e)}\n")
        return False
    
    finally:
        scraper.close()


def main():
    """Main execution function - runs both scrapers in sequence."""
    print("="*80)
    print("UNIFIED WEB SCRAPER - YELLOW PAGES + FACEBOOK EMAIL")
    print("="*80)
    print()
    
    job_type = input("Enter the Job Type (e.g., Plumber, Restaurant, Dentist): ").strip()
    location = input("Enter the Location (e.g., Los Angeles CA, New York NY): ").strip()
    
    if not job_type or not location:
        print("\nERROR: Both Job Type and Location are required.")
        return
    
    print("\n" + "="*80)
    print("PHASE 1: YELLOW PAGES SCRAPING")
    print("="*80 + "\n")
    
    yp_scraper = None
    excel_file = None
    results = []
    
    try:
        # PHASE 1: Yellow Pages Scraping
        yp_scraper = YellowPagesScraper()
        yp_scraper.navigate_to_site()
        yp_scraper.perform_search(job_type, location)
        
        print("="*80)
        print("STARTING DATA EXTRACTION FROM YELLOW PAGES")
        print("="*80)
        print("This may take several minutes depending on the number of results...")
        print("Progress will be shown as listings are extracted.\n")
        
        results = yp_scraper.extract_listings(job_type=job_type, location=location)
        
        if results:
            excel_file = save_to_excel(results, job_type, location)
        else:
            print("\nNo results found to save.")
            return
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  SCRAPING INTERRUPTED BY USER")
        if results:
            print(f"Saving {len(results)} listings collected before interruption...\n")
            excel_file = save_to_excel(results, job_type, location)
        else:
            print("No data to save.\n")
        return
    except Exception as e:
        print(f"\nFATAL ERROR: {str(e)}")
        print("Scraping process failed.")
        return
    
    finally:
        if yp_scraper:
            print("\nKeeping browser open for 3 seconds...")
            time.sleep(3)
            yp_scraper.close()
    
    # PHASE 2: Facebook Email Extraction
    if excel_file:
        print("\n" + "="*80)
        print("PHASE 2: FACEBOOK EMAIL EXTRACTION")
        print("="*80)
        
        process_excel_for_emails(excel_file)
    
    print("\n" + "="*80)
    print("✓ COMPLETE! UNIFIED SCRAPING FINISHED")
    print("="*80)
    print(f"Final Excel file: {excel_file}")
    print("All data (Business Name, Phone Number, Email) saved in one file!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()