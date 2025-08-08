import requests
from bs4 import BeautifulSoup
import json

def test_website_structure():
    url = "https://atsogo.mw/listings/properties"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Save the HTML to a file for inspection
        with open('atsogo_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print("HTML saved to atsogo_page.html")
        
        # Look for property listings
        print("\nSearching for property elements...")
        
        # Try different selectors
        selectors = [
            'div[class*="listin"]',
            'div[class*="property"]',
            'div[class*="listing"]',
            'div[class*="item"]',
            '.listin',
            '.property',
            '.listing'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            print(f"Selector '{selector}': {len(elements)} elements found")
            if elements:
                print(f"First element classes: {elements[0].get('class', [])}")
                print(f"First element text preview: {elements[0].get_text()[:200]}...")
                break
        
        # Look for any divs with property-related text
        all_divs = soup.find_all('div')
        property_divs = []
        
        for div in all_divs:
            text = div.get_text().lower()
            if any(keyword in text for keyword in ['plot', 'house', 'land', 'commercial', 'for sale', 'for rent', 'mk']):
                property_divs.append(div)
        
        print(f"\nFound {len(property_divs)} divs with property-related content")
        
        if property_divs:
            print("Sample property div:")
            sample = property_divs[0]
            print(f"Classes: {sample.get('class', [])}")
            print(f"Text: {sample.get_text()[:300]}...")
        
        # Look for h3 elements (property titles)
        h3_elements = soup.find_all('h3')
        print(f"\nFound {len(h3_elements)} h3 elements")
        for i, h3 in enumerate(h3_elements[:5]):
            print(f"H3 {i+1}: {h3.get_text().strip()}")
        
        # Look for strong elements (prices)
        strong_elements = soup.find_all('strong')
        print(f"\nFound {len(strong_elements)} strong elements")
        for i, strong in enumerate(strong_elements[:5]):
            print(f"Strong {i+1}: {strong.get_text().strip()}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_website_structure()
