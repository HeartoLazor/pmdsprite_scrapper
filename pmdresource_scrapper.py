from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
import csv
import re
import time
import argparse

INPUT_POKEMON_CSV = "pokemon_data.csv"
OUT_POKEMON_CSV = "pokemon_selenium.csv"
SEPARATOR = ";"
POKEMON_RANGE_START = 1
POKEMON_RANGE_END = 1025
RESTART_AFTER = 1

def create_driver():
    """Create a new Chrome driver instance"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def scrape_with_selenium():
    """Use Selenium to handle JavaScript with Material-UI"""
    
    driver = create_driver()
    variations_data = {}
    processed_count = 0
    
    try:
        with open(INPUT_POKEMON_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            pokemon_list = list(reader)
        
        # Filter by range
        pokemon_to_process = [
            row for row in pokemon_list 
            if POKEMON_RANGE_START <= int(row['number']) <= POKEMON_RANGE_END
        ]
        
        print(f"Processing Pokémon from {POKEMON_RANGE_START} to {POKEMON_RANGE_END}...")
        
        for row in pokemon_to_process:
            pokemon_id = row['number'].zfill(4)
            pokemon_name = row['name']
            
            # Restart driver every RESTART_AFTER Pokémon
            if processed_count > 0 and processed_count % RESTART_AFTER == 0:
                print(f"🔄 Restarting driver after {processed_count} Pokémon...")
                driver.quit()
                driver = create_driver()
                time.sleep(2)
            
            print(f"Processing {pokemon_id} - {pokemon_name}...")
            processed_count += 1
            
            try:
                driver.get(f"https://sprites.pmdcollab.org/#/{pokemon_id}")
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(2)
                
                variations_paths = []
                variation_types = []
                
                # Find dropdown with timeout
                try:
                    dropdown = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "[role='button'][aria-haspopup='listbox']"))
                    )
                    print(f"  Dropdown found: '{dropdown.text}'")
                    
                    # Get option texts first
                    dropdown.click()
                    time.sleep(1)
                    
                    option_elements = driver.find_elements(By.CSS_SELECTOR, "[role='option']")
                    option_texts = [opt.text.strip() for opt in option_elements]
                    print(f"  Available options: {option_texts}")
                    
                    # Close initial dropdown
                    driver.find_element(By.TAG_NAME, "body").click()
                    time.sleep(1)
                    
                    # Process each option (INCLUDING Normal)
                    for option_text in option_texts:
                        print(f"  Processing: {option_text}")
                        
                        try:
                            # Reopen dropdown
                            dropdown = driver.find_element(By.CSS_SELECTOR, "[role='button'][aria-haspopup='listbox']")
                            dropdown.click()
                            time.sleep(1)
                            
                            # Find and click specific option
                            option_xpath = f"//*[@role='option' and normalize-space()='{option_text}']"
                            option = driver.find_element(By.XPATH, option_xpath)
                            option.click()
                            time.sleep(2)
                            
                            # Find download URL with timeout
                            try:
                                download_links = WebDriverWait(driver, 5).until(
                                    EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, 'sprites.zip')]"))
                                )
                                
                                download_url_found = None
                                for link in download_links:
                                    download_url = link.get_attribute('href')
                                    if download_url:
                                        download_url_found = download_url
                                        break
                                
                                # Only process if we found download URL
                                if download_url_found:
                                    print(f"    URL found: {download_url_found}")
                                    
                                    # Extract complete URL pattern
                                    match = re.search(r'/(\d{4}(?:/\d{4})*)/sprites\.zip$', download_url_found)
                                    
                                    if match:
                                        path_segment = match.group(1)
                                        minimal_code = f"{path_segment}/"
                                        variations_paths.append(minimal_code)
                                        variation_types.append(option_text)
                                        print(f"    ✓ {option_text} -> {minimal_code}")
                                    else:
                                        print(f"    ⚠ Could not extract URL pattern: {download_url_found}")
                                else:
                                    print(f"    ⚠ No download URL found for {option_text}, ignoring...")
                                
                            except TimeoutException:
                                print(f"    ⚠ Timeout finding download URL for {option_text}")
                                continue
                            
                        except StaleElementReferenceException:
                            print(f"    ⚠ Stale element, retrying {option_text}...")
                            continue
                        except Exception as e:
                            print(f"    Error with {option_text}: {e}")
                            continue
                    
                    if variations_paths:
                        variations_data[pokemon_id] = {
                            'variations_paths': variations_paths,
                            'variation_types': variation_types
                        }
                        print(f"  ✅ Variations found: {len(variation_types)}")
                    else:
                        print(f"  ⚠ No variations with download URLs found")
                    
                except TimeoutException:
                    print(f"  ⚠ Timeout finding dropdown for {pokemon_id}")
                    continue
                
                time.sleep(1)
                
            except Exception as e:
                print(f"  ❌ Error processing {pokemon_id}: {e}")
                # Try to recover by restarting driver on major errors
                try:
                    driver.quit()
                    driver = create_driver()
                    print("  🔄 Driver restarted after error")
                    time.sleep(2)
                except:
                    pass
                continue
                
    finally:
        driver.quit()
    
    return variations_data

def update_minimal_variants_only():
    """Only update minimal_variants column without scraping"""
    print("Updating minimal_variants column only...")
    
    with open(INPUT_POKEMON_CSV, 'r', encoding='utf-8') as infile, \
         open(OUT_POKEMON_CSV, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        
        # Add minimal_variants to fieldnames if it doesn't exist
        if 'minimal_variants' not in fieldnames:
            fieldnames = list(fieldnames) + ['minimal_variants']
        
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        updated_count = 0
        total_rows = 0
        
        for row in reader:
            total_rows += 1
            
            # Check if we have variations data
            if 'variations_paths' in row and row['variations_paths']:
                variations_count = len(row['variations_paths'].split(SEPARATOR))
                
                # Generate or update minimal_variants
                if 'minimal_variants' in row and row['minimal_variants']:
                    # If minimal_variants already exists, adjust to match variations count
                    existing_minimal = row['minimal_variants'].split(SEPARATOR)
                    
                    if len(existing_minimal) > variations_count:
                        # Remove extra elements if we have more minimal_variants than variations
                        row['minimal_variants'] = SEPARATOR.join(existing_minimal[:variations_count])
                        updated_count += 1
                        print(f"Removed extra minimal_variants for {row['number']} - {row['name']}")
                    elif len(existing_minimal) < variations_count:
                        # Add '1's if we have fewer minimal_variants than variations
                        additional_ones = ['1'] * (variations_count - len(existing_minimal))
                        row['minimal_variants'] = SEPARATOR.join(existing_minimal + additional_ones)
                        updated_count += 1
                        print(f"Added missing minimal_variants for {row['number']} - {row['name']}")
                    # If counts match, preserve existing values
                else:
                    # If no minimal_variants exists, create all '1's
                    row['minimal_variants'] = SEPARATOR.join(['1'] * variations_count)
                    updated_count += 1
                    print(f"Created minimal_variants for {row['number']} - {row['name']}")
            else:
                # For Pokémon without variations data, ensure minimal_variants exists but empty
                if 'minimal_variants' not in row or not row['minimal_variants']:
                    row['minimal_variants'] = ''
            
            writer.writerow(row)
        
        print(f"Total rows processed: {total_rows}")
        print(f"Pokémon updated: {updated_count}")

def update_csv_selenium():
    """Update CSV with Selenium data"""
    print("Starting Selenium scraping...")
    variations_data = scrape_with_selenium()
    
    print(f"Data obtained for {len(variations_data)} Pokémon")
    
    with open(INPUT_POKEMON_CSV, 'r', encoding='utf-8') as infile, \
         open(OUT_POKEMON_CSV, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        
        # Add minimal_variants to fieldnames if it doesn't exist
        if 'minimal_variants' not in fieldnames:
            fieldnames = list(fieldnames) + ['minimal_variants']
        
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        updated_count = 0
        total_rows = 0
        
        for row in reader:
            total_rows += 1
            pokemon_id = row['number'].zfill(4)
            
            if pokemon_id in variations_data:
                row['variations_paths'] = SEPARATOR.join(variations_data[pokemon_id]['variations_paths'])
                row['variation_types'] = SEPARATOR.join(variations_data[pokemon_id]['variation_types'])
                
                # Generate minimal_variants - preserve existing values if they exist
                num_variations = len(variations_data[pokemon_id]['variations_paths'])
                
                if 'minimal_variants' in row and row['minimal_variants']:
                    # If minimal_variants already exists, adjust to match current variations count
                    existing_minimal = row['minimal_variants'].split(SEPARATOR)
                    
                    if len(existing_minimal) > num_variations:
                        # Remove extra elements if we have more minimal_variants than variations
                        row['minimal_variants'] = SEPARATOR.join(existing_minimal[:num_variations])
                    elif len(existing_minimal) < num_variations:
                        # Add '1's if we have fewer minimal_variants than variations
                        additional_ones = ['1'] * (num_variations - len(existing_minimal))
                        row['minimal_variants'] = SEPARATOR.join(existing_minimal + additional_ones)
                    # If counts match, preserve existing values
                else:
                    # If no minimal_variants exists, create all '1's
                    row['minimal_variants'] = SEPARATOR.join(['1'] * num_variations)
                
                updated_count += 1
            else:
                # For Pokémon without variations data, ensure minimal_variants exists
                if 'minimal_variants' not in row or not row['minimal_variants']:
                    row['minimal_variants'] = ''
            
            writer.writerow(row)
        
        print(f"Total rows processed: {total_rows}")
        print(f"Pokémon updated: {updated_count}")
    
    print(f"Output file created: {OUT_POKEMON_CSV}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='PMD Sprite Scraper')
    parser.add_argument('--minimal-only', action='store_true', 
                       help='Only update minimal_variants column without scraping')
    
    args = parser.parse_args()
    
    if args.minimal_only:
        update_minimal_variants_only()
    else:
        update_csv_selenium()