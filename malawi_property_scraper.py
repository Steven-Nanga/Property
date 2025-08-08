import requests
from bs4 import BeautifulSoup
import csv
import time
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MalawiPropertyScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_page_content(self, url, timeout=25):
        """Fetch page content with error handling"""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text.strip())
    
    def extract_price(self, text):
        """Extract price from text"""
        if not text:
            return ""
        
        patterns = [
            r'MK\s*([\d,]+\.?\d*)',
            r'MWK\s*([\d,]+\.?\d*)',
            r'K\s*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*MK',
            r'([\d,]+\.?\d*)\s*MWK',
            r'([\d,]+\.?\d*)\s*K',
            r'\$([\d,]+\.?\d*)',
            r'USD\s*([\d,]+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).replace(',', '')
        
        return ""
    
    def extract_area(self, text):
        """Extract area from text"""
        if not text:
            return ""
        
        patterns = [
            r'(\d+)\s*sqm',
            r'(\d+)\s*m²',
            r'(\d+)\s*square\s*meters',
            r'(\d+)\s*hectares',
            r'(\d+)\s*ha'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""
    
    def extract_bedrooms_bathrooms(self, text):
        """Extract bedrooms and bathrooms from text"""
        if not text:
            return "", ""
        
        bed_patterns = [
            r'(\d+)\s*beds?',
            r'(\d+)\s*bedrooms?'
        ]
        
        bath_patterns = [
            r'(\d+)\s*baths?',
            r'(\d+)\s*bathrooms?',
            r'(\d+)\s*showers?'
        ]
        
        bedrooms = ""
        bathrooms = ""
        
        for pattern in bed_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                bedrooms = match.group(1)
                break
        
        for pattern in bath_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                bathrooms = match.group(1)
                break
        
        return bedrooms, bathrooms
    
    def scrape_atsogo(self, max_pages=None):
        """Scrape properties from Atsogo website"""
        logger.info("Scraping Atsogo properties...")
        properties = []
        page = 1
        
        while True:
            if max_pages and page > max_pages:
                break
                
            url = f"https://atsogo.mw/listings/properties?page={page}" if page > 1 else "https://atsogo.mw/listings/properties"
            content = self.get_page_content(url)
            
            if not content:
                break
            
            soup = BeautifulSoup(content, 'html.parser')
            property_elements = soup.find_all('div', class_='property_item')
            
            if not property_elements:
                break
            
            for prop_elem in property_elements:
                try:
                    all_text = prop_elem.get_text()
                    lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                    
                    property_data = {
                        'source': 'atsogo',
                        'title': '',
                        'property_type': '',
                        'transaction_type': '',
                        'location': '',
                        'price': '',
                        'area_sqm': '',
                        'bedrooms': '',
                        'bathrooms': '',
                        'date_posted': '',
                        'description': '',
                        'url': url
                    }
                    
                    # Extract title
                    title_elem = prop_elem.find('h3')
                    if title_elem:
                        property_data['title'] = self.clean_text(title_elem.get_text())
                    
                    # Extract property type and transaction type
                    for i, line in enumerate(lines):
                        if line in ['Plot', 'Complete House', 'Land', 'Commercial Property', 'Incompleted House']:
                            property_data['property_type'] = line
                            if i + 1 < len(lines) and lines[i + 1] in ['For Sale', 'For rent']:
                                property_data['transaction_type'] = lines[i + 1]
                            break
                    
                    # Extract location
                    location_match = re.search(r'(LILONGWE|BLANTYRE|SALIMA|NKHOTAKOTA|MZIMBA|MZUZU|ZOMBA|THYOLO|RUMPHI|NENO|NKHATABAY|NTCHISI|NTCHEU|NSANJE|MCHINJI|MULANJE|MANGOCHI|MACHINGA|LIWONDE|KARONGA|KASUNGU|DOWA|DEDZA|CHIRADZULU|CHIKWAWA|CHITIPA|BALAKA)[^,\n]*', all_text)
                    if location_match:
                        for line in lines:
                            if location_match.group(1) in line:
                                property_data['location'] = line.strip()
                                break
                    
                    # Extract other details
                    property_data['price'] = self.extract_price(all_text)
                    property_data['area_sqm'] = self.extract_area(all_text)
                    
                    bed_bath_match = re.search(r'(\d+)\s+(\d+)\s+Bathroom', all_text)
                    if bed_bath_match:
                        property_data['bedrooms'] = bed_bath_match.group(1)
                        property_data['bathrooms'] = bed_bath_match.group(2)
                    
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', all_text)
                    if date_match:
                        property_data['date_posted'] = date_match.group(1)
                    
                    properties.append(property_data)
                    
                except Exception as e:
                    logger.error(f"Error extracting Atsogo property: {e}")
            
            page += 1
            time.sleep(1)
        
        logger.info(f"Scraped {len(properties)} properties from Atsogo")
        return properties
    
    def scrape_sgw(self, max_pages=None):
        """Scrape properties from SGW website"""
        logger.info("Scraping SGW properties...")
        properties = []
        
        try:
            # Try multiple URLs for SGW
            urls_to_try = [
                "https://sgw.mw",
                "https://sgw.mw/properties",
                "https://sgw.mw/listings"
            ]
            
            content = None
            for url in urls_to_try:
                logger.info(f"Trying SGW URL: {url}")
                content = self.get_page_content(url, timeout=30)
                if content:
                    break
            
            if not content:
                logger.error("Could not fetch any SGW URLs")
                return properties
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for property listings with various selectors
            selectors = [
                'div[class*="property"]',
                'div[class*="listing"]',
                'div[class*="item"]',
                'article[class*="property"]',
                'article[class*="listing"]',
                '.property-item',
                '.listing-item',
                '.property-card',
                '.listing-card'
            ]
            
            property_elements = []
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    property_elements = elements
                    logger.info(f"Found {len(elements)} property elements using selector: {selector}")
                    break
            
            # If no specific selectors work, look for any div with property-related text
            if not property_elements:
                all_divs = soup.find_all('div')
                for div in all_divs:
                    text = div.get_text().lower()
                    if any(keyword in text for keyword in ['mk', 'price', 'bed', 'bath', 'house', 'plot', 'land', 'rent', 'sale']):
                        if len(text) > 50:  # Only consider substantial content
                            property_elements.append(div)
                logger.info(f"Found {len(property_elements)} potential property divs by text analysis")
            
            for prop_elem in property_elements:
                try:
                    all_text = prop_elem.get_text()
                    
                    property_data = {
                        'source': 'sgw',
                        'title': '',
                        'property_type': '',
                        'transaction_type': '',
                        'location': '',
                        'price': '',
                        'area_sqm': '',
                        'bedrooms': '',
                        'bathrooms': '',
                        'date_posted': '',
                        'description': '',
                        'url': 'https://sgw.mw'
                    }
                    
                    # Extract title
                    title_elem = prop_elem.find(['h1', 'h2', 'h3', 'h4'])
                    if title_elem:
                        property_data['title'] = self.clean_text(title_elem.get_text())
                    
                    # Extract price
                    property_data['price'] = self.extract_price(all_text)
                    
                    # Extract location
                    location_match = re.search(r'(Blantyre|Lilongwe|Mzuzu|Zomba|Limbe|Mangochi|Salima|Nkhotakota|Mchinji|Dowa|Dedza|Ntcheu|Ntchisi|Nkhatabay|Rumphi|Chitipa|Karonga|Kasungu|Machinga|Mulanje|Thyolo|Chikwawa|Nsanje|Chirazulu|Balaka|Neno)[^,\n]*', all_text, re.IGNORECASE)
                    if location_match:
                        property_data['location'] = location_match.group(0).strip()
                    
                    # Extract bedrooms and bathrooms
                    bedrooms, bathrooms = self.extract_bedrooms_bathrooms(all_text)
                    property_data['bedrooms'] = bedrooms
                    property_data['bathrooms'] = bathrooms
                    
                    # Extract area
                    property_data['area_sqm'] = self.extract_area(all_text)
                    
                    # Determine transaction type
                    if 'rent' in all_text.lower() or 'let' in all_text.lower():
                        property_data['transaction_type'] = 'For Rent'
                    elif 'sale' in all_text.lower():
                        property_data['transaction_type'] = 'For Sale'
                    
                    # Determine property type
                    if any(word in all_text.lower() for word in ['house', 'home', 'residential']):
                        property_data['property_type'] = 'Residential'
                    elif any(word in all_text.lower() for word in ['commercial', 'office', 'shop', 'warehouse']):
                        property_data['property_type'] = 'Commercial'
                    elif any(word in all_text.lower() for word in ['plot', 'land']):
                        property_data['property_type'] = 'Land'
                    
                    if property_data['title'] or property_data['price']:
                        properties.append(property_data)
                    
                except Exception as e:
                    logger.error(f"Error extracting SGW property: {e}")
        
        except Exception as e:
            logger.error(f"Error scraping SGW: {e}")
        
        logger.info(f"Scraped {len(properties)} properties from SGW")
        return properties
    
    def scrape_knightfrank(self, max_pages=None):
        """Scrape properties from Knight Frank website"""
        logger.info("Scraping Knight Frank properties...")
        properties = []
        
        try:
            content = self.get_page_content("https://www.knightfrank.mw", timeout=30)
            if not content:
                return properties
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for property listings with various approaches
            selectors = [
                'div[class*="property"]',
                'div[class*="listing"]',
                'div[class*="item"]',
                'article[class*="property"]',
                'article[class*="listing"]',
                '.property-item',
                '.listing-item',
                '.property-card',
                '.listing-card'
            ]
            
            property_elements = []
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    property_elements = elements
                    logger.info(f"Found {len(elements)} property elements using selector: {selector}")
                    break
            
            # If no specific selectors work, look for any div with property-related text
            if not property_elements:
                all_divs = soup.find_all('div')
                for div in all_divs:
                    text = div.get_text().lower()
                    if any(keyword in text for keyword in ['mk', 'price', 'bed', 'bath', 'house', 'plot', 'land', 'rent', 'sale']):
                        if len(text) > 50:  # Only consider substantial content
                            property_elements.append(div)
                logger.info(f"Found {len(property_elements)} potential property divs by text analysis")
            
            for prop_elem in property_elements:
                try:
                    all_text = prop_elem.get_text()
                    
                    property_data = {
                        'source': 'knightfrank',
                        'title': '',
                        'property_type': '',
                        'transaction_type': '',
                        'location': '',
                        'price': '',
                        'area_sqm': '',
                        'bedrooms': '',
                        'bathrooms': '',
                        'date_posted': '',
                        'description': '',
                        'url': 'https://www.knightfrank.mw'
                    }
                    
                    # Extract title
                    title_elem = prop_elem.find(['h1', 'h2', 'h3', 'h4', 'h5'])
                    if title_elem:
                        property_data['title'] = self.clean_text(title_elem.get_text())
                    
                    # Extract price
                    property_data['price'] = self.extract_price(all_text)
                    
                    # Extract location
                    location_match = re.search(r'(Blantyre|Lilongwe|Mzuzu|Zomba|Limbe|Mangochi|Salima|Nkhotakota|Mchinji|Dowa|Dedza|Ntcheu|Ntchisi|Nkhatabay|Rumphi|Chitipa|Karonga|Kasungu|Machinga|Mulanje|Thyolo|Chikwawa|Nsanje|Chirazulu|Balaka|Neno)[^,\n]*', all_text, re.IGNORECASE)
                    if location_match:
                        property_data['location'] = location_match.group(0).strip()
                    
                    # Extract bedrooms and bathrooms
                    bedrooms, bathrooms = self.extract_bedrooms_bathrooms(all_text)
                    property_data['bedrooms'] = bedrooms
                    property_data['bathrooms'] = bathrooms
                    
                    # Extract area
                    property_data['area_sqm'] = self.extract_area(all_text)
                    
                    if property_data['title'] or property_data['price']:
                        properties.append(property_data)
                    
                except Exception as e:
                    logger.error(f"Error extracting Knight Frank property: {e}")
        
        except Exception as e:
            logger.error(f"Error scraping Knight Frank: {e}")
        
        logger.info(f"Scraped {len(properties)} properties from Knight Frank")
        return properties
    
    def scrape_nyumba24(self, max_pages=None):
        """Scrape properties from Nyumba24 website"""
        logger.info("Scraping Nyumba24 properties...")
        properties = []
        
        try:
            content = self.get_page_content("https://www.nyumba24.com")
            if not content:
                return properties
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for property listings
            property_elements = soup.find_all(['div', 'article'], class_=re.compile(r'property|listing|item|card', re.IGNORECASE))
            
            for prop_elem in property_elements:
                try:
                    all_text = prop_elem.get_text()
                    
                    property_data = {
                        'source': 'nyumba24',
                        'title': '',
                        'property_type': '',
                        'transaction_type': '',
                        'location': '',
                        'price': '',
                        'area_sqm': '',
                        'bedrooms': '',
                        'bathrooms': '',
                        'date_posted': '',
                        'description': '',
                        'url': 'https://www.nyumba24.com'
                    }
                    
                    # Extract title
                    title_elem = prop_elem.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    if title_elem:
                        property_data['title'] = self.clean_text(title_elem.get_text())
                    
                    # Extract price
                    property_data['price'] = self.extract_price(all_text)
                    
                    # Extract location
                    location_match = re.search(r'(Blantyre|Lilongwe|Mzuzu|Zomba|Limbe|Mangochi|Salima|Nkhotakota|Mchinji|Dowa|Dedza|Ntcheu|Ntchisi|Nkhatabay|Rumphi|Chitipa|Karonga|Kasungu|Machinga|Mulanje|Thyolo|Chikwawa|Nsanje|Chirazulu|Balaka|Neno)[^,\n]*', all_text, re.IGNORECASE)
                    if location_match:
                        property_data['location'] = location_match.group(0).strip()
                    
                    # Extract bedrooms and bathrooms
                    bedrooms, bathrooms = self.extract_bedrooms_bathrooms(all_text)
                    property_data['bedrooms'] = bedrooms
                    property_data['bathrooms'] = bathrooms
                    
                    # Extract area
                    property_data['area_sqm'] = self.extract_area(all_text)
                    
                    # Determine transaction type
                    if 'rent' in all_text.lower():
                        property_data['transaction_type'] = 'For Rent'
                    elif 'sale' in all_text.lower():
                        property_data['transaction_type'] = 'For Sale'
                    
                    if property_data['title'] or property_data['price']:
                        properties.append(property_data)
                    
                except Exception as e:
                    logger.error(f"Error extracting Nyumba24 property: {e}")
        
        except Exception as e:
            logger.error(f"Error scraping Nyumba24: {e}")
        
        logger.info(f"Scraped {len(properties)} properties from Nyumba24")
        return properties
    
    def scrape_reynolds(self, max_pages=None):
        """Scrape properties from Reynolds website"""
        logger.info("Scraping Reynolds properties...")
        properties = []
        
        try:
            content = self.get_page_content("https://reynolds.mw", timeout=30)
            if not content:
                return properties
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for property listings
            selectors = [
                'div[class*="property"]',
                'div[class*="listing"]',
                'div[class*="item"]',
                'article[class*="property"]',
                'article[class*="listing"]',
                '.property-item',
                '.listing-item',
                '.property-card',
                '.listing-card'
            ]
            
            property_elements = []
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    property_elements = elements
                    logger.info(f"Found {len(elements)} property elements using selector: {selector}")
                    break
            
            # If no specific selectors work, look for any div with property-related text
            if not property_elements:
                all_divs = soup.find_all('div')
                for div in all_divs:
                    text = div.get_text().lower()
                    if any(keyword in text for keyword in ['mk', 'price', 'bed', 'bath', 'house', 'plot', 'land', 'rent', 'sale']):
                        if len(text) > 50:  # Only consider substantial content
                            property_elements.append(div)
                logger.info(f"Found {len(property_elements)} potential property divs by text analysis")
            
            for prop_elem in property_elements:
                try:
                    all_text = prop_elem.get_text()
                    
                    property_data = {
                        'source': 'reynolds',
                        'title': '',
                        'property_type': '',
                        'transaction_type': '',
                        'location': '',
                        'price': '',
                        'area_sqm': '',
                        'bedrooms': '',
                        'bathrooms': '',
                        'date_posted': '',
                        'description': '',
                        'url': 'https://reynolds.mw'
                    }
                    
                    # Extract title
                    title_elem = prop_elem.find(['h1', 'h2', 'h3', 'h4', 'h5'])
                    if title_elem:
                        property_data['title'] = self.clean_text(title_elem.get_text())
                    
                    # Extract price
                    property_data['price'] = self.extract_price(all_text)
                    
                    # Extract location
                    location_match = re.search(r'(Blantyre|Lilongwe|Mzuzu|Zomba|Limbe|Mangochi|Salima|Nkhotakota|Mchinji|Dowa|Dedza|Ntcheu|Ntchisi|Nkhatabay|Rumphi|Chitipa|Karonga|Kasungu|Machinga|Mulanje|Thyolo|Chikwawa|Nsanje|Chirazulu|Balaka|Neno)[^,\n]*', all_text, re.IGNORECASE)
                    if location_match:
                        property_data['location'] = location_match.group(0).strip()
                    
                    # Extract bedrooms and bathrooms
                    bedrooms, bathrooms = self.extract_bedrooms_bathrooms(all_text)
                    property_data['bedrooms'] = bedrooms
                    property_data['bathrooms'] = bathrooms
                    
                    # Extract area
                    property_data['area_sqm'] = self.extract_area(all_text)
                    
                    if property_data['title'] or property_data['price']:
                        properties.append(property_data)
                    
                except Exception as e:
                    logger.error(f"Error extracting Reynolds property: {e}")
        
        except Exception as e:
            logger.error(f"Error scraping Reynolds: {e}")
        
        logger.info(f"Scraped {len(properties)} properties from Reynolds")
        return properties
    
    def scrape_4321property(self, max_pages=None):
        """Scrape properties from 4321 Property website"""
        logger.info("Scraping 4321 Property properties...")
        properties = []
        
        try:
            content = self.get_page_content("https://www.4321property.com/malawi", timeout=30)
            if not content:
                return properties
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for property listings
            selectors = [
                'div[class*="property"]',
                'div[class*="listing"]',
                'div[class*="item"]',
                'article[class*="property"]',
                'article[class*="listing"]',
                '.property-item',
                '.listing-item',
                '.property-card',
                '.listing-card'
            ]
            
            property_elements = []
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    property_elements = elements
                    logger.info(f"Found {len(elements)} property elements using selector: {selector}")
                    break
            
            # If no specific selectors work, look for any div with property-related text
            if not property_elements:
                all_divs = soup.find_all('div')
                for div in all_divs:
                    text = div.get_text().lower()
                    if any(keyword in text for keyword in ['mk', 'price', 'bed', 'bath', 'house', 'plot', 'land', 'rent', 'sale']):
                        if len(text) > 50:  # Only consider substantial content
                            property_elements.append(div)
                logger.info(f"Found {len(property_elements)} potential property divs by text analysis")
            
            for prop_elem in property_elements:
                try:
                    all_text = prop_elem.get_text()
                    
                    property_data = {
                        'source': '4321property',
                        'title': '',
                        'property_type': '',
                        'transaction_type': '',
                        'location': '',
                        'price': '',
                        'area_sqm': '',
                        'bedrooms': '',
                        'bathrooms': '',
                        'date_posted': '',
                        'description': '',
                        'url': 'https://www.4321property.com/malawi'
                    }
                    
                    # Extract title
                    title_elem = prop_elem.find(['h1', 'h2', 'h3', 'h4', 'h5'])
                    if title_elem:
                        property_data['title'] = self.clean_text(title_elem.get_text())
                    
                    # Extract price
                    property_data['price'] = self.extract_price(all_text)
                    
                    # Extract location
                    location_match = re.search(r'(Blantyre|Lilongwe|Mzuzu|Zomba|Limbe|Mangochi|Salima|Nkhotakota|Mchinji|Dowa|Dedza|Ntcheu|Ntchisi|Nkhatabay|Rumphi|Chitipa|Karonga|Kasungu|Machinga|Mulanje|Thyolo|Chikwawa|Nsanje|Chirazulu|Balaka|Neno)[^,\n]*', all_text, re.IGNORECASE)
                    if location_match:
                        property_data['location'] = location_match.group(0).strip()
                    
                    # Extract bedrooms and bathrooms
                    bedrooms, bathrooms = self.extract_bedrooms_bathrooms(all_text)
                    property_data['bedrooms'] = bedrooms
                    property_data['bathrooms'] = bathrooms
                    
                    # Extract area
                    property_data['area_sqm'] = self.extract_area(all_text)
                    
                    if property_data['title'] or property_data['price']:
                        properties.append(property_data)
                    
                except Exception as e:
                    logger.error(f"Error extracting 4321 Property property: {e}")
        
        except Exception as e:
            logger.error(f"Error scraping 4321 Property: {e}")
        
        logger.info(f"Scraped {len(properties)} properties from 4321 Property")
        return properties
    
    def scrape_all_websites(self, max_pages_per_site=None):
        """Scrape properties from all websites"""
        all_properties = []
        
        # Scrape from each website
        scrapers = [
            ('atsogo', self.scrape_atsogo),
            ('sgw', self.scrape_sgw),
            ('knightfrank', self.scrape_knightfrank),
            ('nyumba24', self.scrape_nyumba24),
            ('reynolds', self.scrape_reynolds),
            ('4321property', self.scrape_4321property)
        ]
        
        for site_name, scraper_func in scrapers:
            try:
                logger.info(f"Starting to scrape {site_name}...")
                properties = scraper_func(max_pages_per_site)
                all_properties.extend(properties)
                logger.info(f"Completed scraping {site_name}. Found {len(properties)} properties.")
                time.sleep(3)  # Be respectful between sites
            except Exception as e:
                logger.error(f"Error scraping {site_name}: {e}")
        
        return all_properties
    
    def save_to_csv(self, properties, filename='malawi_properties.csv'):
        """Save scraped properties to CSV file"""
        if not properties:
            logger.warning("No properties to save")
            return
        
        fieldnames = [
            'source', 'title', 'property_type', 'transaction_type', 'location', 
            'price', 'area_sqm', 'bedrooms', 'bathrooms', 'date_posted', 'description', 'url'
        ]
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(properties)
            
            logger.info(f"Successfully saved {len(properties)} properties to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
    
    def run(self, max_pages_per_site=None):
        """Main method to run the scraper"""
        logger.info("Starting Malawi property scraper")
        
        # Scrape properties from all websites
        properties = self.scrape_all_websites(max_pages_per_site)
        
        if properties:
            # Save to CSV
            self.save_to_csv(properties)
            logger.info(f"Scraping completed. Total properties scraped: {len(properties)}")
            
            # Print summary by source
            source_counts = {}
            for prop in properties:
                source = prop['source']
                source_counts[source] = source_counts.get(source, 0) + 1
            
            logger.info("Summary by source:")
            for source, count in source_counts.items():
                logger.info(f"  {source}: {count} properties")
        else:
            logger.warning("No properties were scraped")

def main():
    """Main function to run the scraper"""
    scraper = MalawiPropertyScraper()
    
    # You can limit the number of pages to scrape per site
    # For example: scraper.run(max_pages_per_site=3)
    scraper.run()

if __name__ == "__main__":
    main()
