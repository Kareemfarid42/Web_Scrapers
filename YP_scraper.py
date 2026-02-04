"""
Yellow Pages Web Scraper (yellowpages.com - US Version)
Senior Python Automation Engineer Implementation

This script scrapes business listings from yellowpages.com based on user-provided
job type and location. It uses Selenium with WebDriverWait for robust
interaction with JavaScript-rendered content.

Required packages:
    pip install selenium webdriver-manager openpyxl pandas
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import time
import pandas as pd
from datetime import datetime
import re


import random

class YellowPagesScraper:
    """Scraper class for Yellow Pages (yellowpages.com) website."""
    
    def __init__(self):
        """Initialize the scraper with Undetected Chrome WebDriver."""
        print("Initializing Undetected Chrome WebDriver...")
        
        # Set up Chrome options for undetected-chromedriver
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--start-maximized')
        
        # Initialize undetected chromedriver (specify version to match installed Chrome)
        self.driver = uc.Chrome(options=options, version_main=144)
        self.wait = WebDriverWait(self.driver, 20)
        
        print("WebDriver initialized successfully.\n")
    
    def navigate_to_site(self):
        """Navigate to Yellow Pages homepage."""
        print("Navigating to https://www.yellowpages.com/...")
        self.driver.get("https://www.yellowpages.com/")
        
        # Random sleep to mimic human behavior
        sleep_time = random.uniform(2, 5)
        time.sleep(sleep_time)
        print(f"Page loaded (waited {sleep_time:.2f}s).\n")
    
    def perform_search(self, job_type, location):
        """
        Perform search on Yellow Pages.
        
        Args:
            job_type (str): The type of business to search for (e.g., "Plumber")
            location (str): The location to search in (e.g., "Los Angeles, CA")
        """
        print(f"Searching for: '{job_type}' in '{location}'...")
        
        try:
            # Wait for the page to fully load
            time.sleep(random.uniform(2, 4))
            
            # Find the "Find a business" input field (based on your screenshot)
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
                    print(f"Found 'What' field using: {by} = {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not what_field:
                raise Exception("Could not find 'What' input field with any selector")
            
            # Clear and enter the job type
            what_field.click()
            what_field.clear()
            time.sleep(0.5)
            what_field.send_keys(job_type)
            print(f"✓ Entered '{job_type}' in 'What' field.")
            
            # Find the "Where" input field (based on your screenshot showing "Los Angeles, CA")
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
                    print(f"Found 'Where' field using: {by} = {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not where_field:
                raise Exception("Could not find 'Where' input field with any selector")
            
            # Clear and enter the location
            where_field.click()
            where_field.clear()
            time.sleep(0.5)
            where_field.send_keys(location)
            print(f"✓ Entered '{location}' in 'Where' field.")
            
            # Find and click the search button (yellow "FIND" button)
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
                    print(f"Found search button using: {by} = {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if search_button:
                # Click using JavaScript for reliability
                self.driver.execute_script("arguments[0].click();", search_button)
                print("✓ Search button clicked.\n")
            else:
                # Fallback: press Enter key
                where_field.send_keys(Keys.RETURN)
                print("✓ Submitted search via Enter key.\n")
            
            # Wait for results page to load
            time.sleep(4)
            print(f"Navigated to: {self.driver.current_url}\n")
            
            # Wait for results to appear (yellowpages.com uses different structure)
            self.wait.until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, 
                    ".result, .search-results, .organic, [class*='result']"
                ))
            )
            print("Search results loaded successfully.\n")
            
        except TimeoutException as e:
            print(f"ERROR: Timeout while performing search.")
            print(f"Current URL: {self.driver.current_url}")
            print(f"Page title: {self.driver.title}")
            self.driver.save_screenshot("search_error.png")
            print("Screenshot saved as 'search_error.png'\n")
            raise
        except Exception as e:
            print(f"ERROR: {str(e)}")
            print(f"Current URL: {self.driver.current_url}")
            self.driver.save_screenshot("search_error.png")
            print("Screenshot saved as 'search_error.png'\n")
            raise
    
    def extract_listings(self, max_results=None, max_pages=None, job_type="", location=""):
        """
        Extract business listings from search results across multiple pages.
        
        Args:
            max_results (int): Maximum number of results to extract (default: None = all results)
            max_pages (int): Maximum number of pages to scrape (default: None = all pages)
            
        Returns:
            list: List of dictionaries containing business name and phone number
        """
        if max_results:
            print(f"Extracting up to {max_results} listings...\n")
        else:
            print(f"Extracting ALL listings from all pages...\n")
        
        results = []
        current_page = 1
        
        try:
            # Loop through pages
            while True:
                print(f"{'='*60}")
                print(f"SCRAPING PAGE {current_page}")
                print(f"{'='*60}\n")
                
                # Try multiple possible selectors for listings on yellowpages.com
                listing_selectors = [
                    ".srp-listing",  # Based on your screenshot
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
                            print(f"Found {len(listings)} listings on page {current_page} using selector: {selector}\n")
                            break
                    except:
                        continue
                
                if not listings:
                    print(f"No listings found on page {current_page}. Stopping.")
                    break
                
                # Process each listing on current page
                for idx, listing in enumerate(listings, 1):
                    # Check if we've reached max_results
                    if max_results and len(results) >= max_results:
                        print(f"\nReached maximum of {max_results} results. Stopping.\n")
                        return results
                    
                    print(f"Processing listing #{len(results) + 1} (Page {current_page}, Item {idx})...")
                    
                    try:
                        # Scroll the listing into view (no print, silent operation)
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", listing)
                        time.sleep(0.5)
                        
                        # Extract business name - yellowpages.com specific selectors
                        business_name = "Unknown"
                        name_selectors = [
                            "a.business-name",  # Based on your screenshot
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
                        
                        # Extract phone number - yellowpages.com specific
                        phone_number = "Not Available"
                        phone_found = False
                        
                        # Method 1: Direct phone text (based on screenshot: .phones.phone.primary)
                        phone_selectors = [
                            ".phones.phone.primary",  # Exact from screenshot
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
                                    
                                    # Clean up phone number (remove extra whitespace, newlines)
                                    phone_text = ' '.join(phone_text.split())
                                    
                                    # Check if it looks like a phone number
                                    if phone_text and (phone_text[0].isdigit() or phone_text.startswith('(')):
                                        phone_number = phone_text
                                        phone_found = True
                                        break
                            except:
                                continue
                            
                            if phone_found:
                                break
                        
                        # Method 2: Look for phone links
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
                        
                        # Method 3: Regex search in HTML
                        if not phone_found:
                            try:
                                listing_html = listing.get_attribute('innerHTML')
                                phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
                                matches = re.findall(phone_pattern, listing_html)
                                if matches:
                                    phone_number = matches[0]
                                    phone_found = True
                            except:
                                pass
                        
                        # Add to results
                        if business_name != "Unknown":
                            results.append({
                                "Business Name": business_name,
                                "Phone Number": phone_number
                            })
                            
                            # Print progress and auto-save every 100 listings
                            if len(results) % 100 == 0:
                                print(f"  ✓ Progress: {len(results)} listings extracted so far...")
                                # Auto-save progress
                                print(f"  💾 Auto-saving progress...")
                                save_to_excel(results, job_type, location)
                            elif len(results) % 50 == 0:
                                print(f"  ✓ Progress: {len(results)} listings extracted so far...")
                        
                    except Exception as e:
                        # Silently continue on errors
                        continue
                
                # Check if we've reached max_pages
                if max_pages and current_page >= max_pages:
                    print(f"\nReached maximum of {max_pages} pages. Stopping.\n")
                    break
                
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
                                next_button_found = False
                                break
                            
                            # Scroll to next button
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                            time.sleep(1)
                            
                            # Get current URL
                            old_url = self.driver.current_url
                            
                            # Click next button
                            self.driver.execute_script("arguments[0].click();", next_button)
                            print(f"✓ Clicked 'Next' button (selector: {next_sel})")
                            
                            # Wait for new page to load
                            time.sleep(3)
                            new_url = self.driver.current_url
                            
                            if new_url != old_url:
                                print(f"✓ Successfully navigated to page {current_page + 1}")
                                print(f"  New URL: {new_url}\n")
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
            print(f"Extraction complete. Successfully scraped {len(results)} listings from {current_page} page(s).")
            print(f"{'='*60}\n")
            return results
            
        except KeyboardInterrupt:
            print(f"\n\n⚠️  INTERRUPTED BY USER (Ctrl+C)")
            print(f"Saving {len(results)} listings collected so far...\n")
            return results
        except Exception as e:
            print(f"ERROR during extraction: {str(e)}")
            return results
    
    def close(self):
        """Close the browser and clean up."""
        print("Closing browser...")
        self.driver.quit()
        print("Browser closed.\n")


def save_to_excel(results, job_type, location):
    """
    Save scraped results to an Excel file.
    
    Args:
        results (list): List of dictionaries containing business information
        job_type (str): Job type searched
        location (str): Location searched
    """
    if not results:
        print("No results to save.")
        return None
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Generate filename WITHOUT timestamp (so it uses the same file)
    filename = f"YellowPages_{job_type}_{location}.xlsx"
    
    # Clean filename (remove special characters)
    filename = "".join(c for c in filename if c.isalnum() or c in ('_', '.', '-'))
    
    try:
        # Save to Excel (overwrites existing file with updated data)
        df.to_excel(filename, index=False, sheet_name='Results')
        print(f"\n{'='*80}")
        print(f"✓ SUCCESS! Data saved to Excel file: {filename}")
        print(f"{'='*80}")
        print(f"Total records saved: {len(results)}")
        print(f"Columns: {', '.join(df.columns.tolist())}")
        print(f"{'='*80}\n")
        return filename
        
    except Exception as e:
        print(f"\nERROR saving to Excel: {str(e)}")
        print("Attempting to save as CSV instead...\n")
        
        # Fallback to CSV
        csv_filename = filename.replace('.xlsx', '.csv')
        try:
            df.to_csv(csv_filename, index=False)
            print(f"✓ Data saved to CSV file: {csv_filename}\n")
            return csv_filename
        except Exception as e2:
            print(f"ERROR saving to CSV: {str(e2)}\n")
            return None


def print_summary(results):
    """
    Print a brief summary of scraped results.
    
    Args:
        results (list): List of dictionaries containing business information
    """
    if not results:
        print("No results to display.")
        return
    
    print("\n" + "=" * 80)
    print("SCRAPING SUMMARY")
    print("=" * 80)
    print(f"Total Businesses Scraped: {len(results)}")
    
    # Count how many have phone numbers
    with_phone = sum(1 for r in results if r['Phone Number'] != 'Not Available')
    without_phone = len(results) - with_phone
    
    print(f"  - With Phone Numbers: {with_phone}")
    print(f"  - Without Phone Numbers: {without_phone}")
    print("=" * 80)
    
    # Show first 5 and last 5 results as preview
    print("\nPREVIEW (First 5 Results):")
    print("-" * 80)
    for idx, result in enumerate(results[:5], 1):
        name = result["Business Name"][:50]
        phone = result["Phone Number"]
        print(f"{idx}. {name:<50} | {phone}")
    
    if len(results) > 10:
        print("\n...")
        print(f"\n({len(results) - 10} more results)")
        print("...")
        print("\nPREVIEW (Last 5 Results):")
        print("-" * 80)
        for idx, result in enumerate(results[-5:], len(results) - 4):
            name = result["Business Name"][:50]
            phone = result["Phone Number"]
            print(f"{idx}. {name:<50} | {phone}")
    
    print("=" * 80 + "\n")


def main():
    """Main execution function."""
    print("=" * 80)
    print("YELLOW PAGES WEB SCRAPER (yellowpages.com)")
    print("=" * 80)
    print()
    
    # Get user inputs
    job_type = input("Enter the Job Type (e.g., Plumber, Restaurant, Dentist): ").strip()
    location = input("Enter the Location (e.g., Los Angeles CA, New York NY): ").strip()
    
    if not job_type or not location:
        print("\nERROR: Both Job Type and Location are required.")
        return
    
    print("\n" + "=" * 80 + "\n")
    
    # Initialize scraper
    scraper = None
    
    try:
        scraper = YellowPagesScraper()
        scraper.navigate_to_site()
        scraper.perform_search(job_type, location)
        
        # Extract ALL listings from ALL pages
        print("\n" + "="*80)
        print("STARTING DATA EXTRACTION")
        print("="*80)
        print("This may take several minutes depending on the number of results...")
        print("Progress will be shown every 50 listings.\n")
        
        results = scraper.extract_listings(job_type=job_type, location=location)
        
        # Save to Excel
        if results:
            save_to_excel(results, job_type, location)
            print_summary(results)
        else:
            print("\nNo results found to save.")
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  SCRAPING INTERRUPTED BY USER")
        if 'results' in locals() and results:
            print(f"Saving {len(results)} listings collected before interruption...\n")
            save_to_excel(results, job_type, location)
            print_summary(results)
        else:
            print("No data to save.\n")
    except Exception as e:
        print(f"\nFATAL ERROR: {str(e)}")
        print("Scraping process failed.")
    
    finally:
        if scraper:
            # Keep browser open for 5 seconds so you can see the final state
            print("\nKeeping browser open for 5 seconds...")
            time.sleep(5)
            scraper.close()
    
    print("\nScript execution completed.")


if __name__ == "__main__":
    main()