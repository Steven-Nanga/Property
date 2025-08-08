import requests
from bs4 import BeautifulSoup
import csv
import time
import re
from urllib.parse import urljoin
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AtsogoScraper:
    def __init__(self):
        self.base_url = "https://atsogo.mw"
        self.properties_url = "https://atsogo.mw/listings/properties"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_page_content(self, url):
        """Fetch page content with error handling"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def extract_property_data(self, property_element):
        """Extract data from a single property listing element"""
        try:
            # Initialize data dictionary
            property_data = {
                'title': '',
                'property_type': '',
                'transaction_type': '',
                'location': '',
                'price': '',
                'area_sqm': '',
                'bedrooms': '',
                'bathrooms': '',
                'date_posted': '',
                'description': ''
            }
            
            # Get all text content for parsing
            all_text = property_element.get_text()
            
            # Extract title
            title_elem = property_element.find('h3')
            if title_elem:
                property_data['title'] = title_elem.get_text(strip=True)
            
            # Extract property type and transaction type from text
            lines = [line.strip() for line in all_text.split('\n') if line.strip()]
            
            # Look for property type and transaction type
            for i, line in enumerate(lines):
                if line in ['Plot', 'Complete House', 'Land', 'Commercial Property', 'Incompleted House']:
                    property_data['property_type'] = line
                    # Next line should be transaction type
                    if i + 1 < len(lines) and lines[i + 1] in ['For Sale', 'For rent']:
                        property_data['transaction_type'] = lines[i + 1]
                    break
            
            # Extract location (look for city names)
            location_match = re.search(r'(LILONGWE|BLANTYRE|SALIMA|NKHOTAKOTA|MZIMBA|MZUZU|ZOMBA|THYOLO|RUMPHI|NENO|NKHATABAY|NKHOTAKOTA|NTCHISI|NTCHEU|NSANJE|MCHINJI|MULANJE|MANGOCHI|MACHINGA|LIWONDE|KARONGA|KASUNGU|DOWA|DEDZA|CHIRADZULU|CHIKWAWA|CHITIPA|BALAKA)[^,\n]*', all_text)
            if location_match:
                # Get the full location line
                location_line = location_match.group(0)
                # Find the complete location line
                for line in lines:
                    if location_match.group(1) in line:
                        property_data['location'] = line.strip()
                        break
            
            # Extract price
            price_match = re.search(r'MK\s*([\d,]+\.?\d*)', all_text)
            if price_match:
                property_data['price'] = price_match.group(1).replace(',', '')
            
            # Extract area
            area_match = re.search(r'(\d+)\s*sqm', all_text)
            if area_match:
                property_data['area_sqm'] = area_match.group(1)
            
            # Extract bedrooms and bathrooms
            # Look for patterns like "4 5 Bathroom" or "0 0 Bathroom"
            bed_bath_match = re.search(r'(\d+)\s+(\d+)\s+Bathroom', all_text)
            if bed_bath_match:
                property_data['bedrooms'] = bed_bath_match.group(1)
                property_data['bathrooms'] = bed_bath_match.group(2)
            
            # Extract date posted
            date_match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', all_text)
            if date_match:
                property_data['date_posted'] = date_match.group(1)
            
            return property_data
            
        except Exception as e:
            logger.error(f"Error extracting property data: {e}")
            return None
    
    def scrape_properties(self, max_pages=None):
        """Scrape properties from all pages"""
        all_properties = []
        page = 1
        
        while True:
            logger.info(f"Scraping page {page}")
            
            # Construct URL for current page
            if page == 1:
                url = self.properties_url
            else:
                url = f"{self.properties_url}?page={page}"
            
            # Get page content
            content = self.get_page_content(url)
            if not content:
                logger.warning(f"Could not fetch page {page}")
                break
            
            # Parse HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find property listings
            property_elements = soup.find_all('div', class_='property_item')
            
            if not property_elements:
                logger.info(f"No more properties found on page {page}")
                break
            
            # Extract data from each property
            page_properties = []
            for prop_elem in property_elements:
                property_data = self.extract_property_data(prop_elem)
                if property_data:
                    page_properties.append(property_data)
            
            all_properties.extend(page_properties)
            logger.info(f"Found {len(page_properties)} properties on page {page}")
            
            # Check if we've reached the maximum pages
            if max_pages and page >= max_pages:
                break
            
            # Check if there's a next page
            next_page = soup.find('a', string='Next')
            if not next_page:
                logger.info("No next page found")
                break
            
            page += 1
            time.sleep(1)  # Be respectful to the server
        
        return all_properties
    
    def save_to_csv(self, properties, filename='atsogo_properties.csv'):
        """Save scraped properties to CSV file"""
        if not properties:
            logger.warning("No properties to save")
            return
        
        fieldnames = [
            'title', 'property_type', 'transaction_type', 'location', 
            'price', 'area_sqm', 'bedrooms', 'bathrooms', 'date_posted', 'description'
        ]
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(properties)
            
            logger.info(f"Successfully saved {len(properties)} properties to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
    
    def run(self, max_pages=None):
        """Main method to run the scraper"""
        logger.info("Starting Atsogo property scraper")
        
        # Scrape properties
        properties = self.scrape_properties(max_pages)
        
        if properties:
            # Save to CSV
            self.save_to_csv(properties)
            logger.info(f"Scraping completed. Total properties scraped: {len(properties)}")
        else:
            logger.warning("No properties were scraped")

def main():
    """Main function to run the scraper"""
    scraper = AtsogoScraper()
    
    # You can limit the number of pages to scrape by setting max_pages
    # For example: scraper.run(max_pages=3)
    scraper.run()

if __name__ == "__main__":
    main()
