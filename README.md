# Malawi Property Scrapers

This repository contains Python scripts to scrape property listings from multiple Malawian real estate websites and save the data to CSV files. It also includes a Jupyter notebook for data analysis and visualization.

## Available Scrapers

### 1. Atsogo Property Scraper (`atsogo_scraper.py`)
Scrapes property listings from the Atsogo website (https://atsogo.mw/listings/properties).

### 2. Multi-Site Property Scraper (`malawi_property_scraper.py`)
Scrapes property listings from multiple Malawian property websites:
- **Atsogo** (https://atsogo.mw)
- **SGW Auctioneers and Estate Agents** (https://sgw.mw)
- **Nyumba24** (https://www.nyumba24.com)
- **Knight Frank** (https://www.knightfrank.mw) - Basic support
- **Reynolds** (https://reynolds.mw) - Basic support
- **4321 Property** (https://www.4321property.com/malawi) - Basic support

## Features

- Scrapes property details including title, type, location, price, area, bedrooms, bathrooms, and posting date
- Handles pagination to scrape multiple pages
- Includes error handling and logging
- Respectful scraping with delays between requests
- Saves data to CSV format
- Multi-site support with unified data format
- **Jupyter notebook for data analysis and visualization**

## Installation

1. Make sure you have Python 3.6+ installed
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Single Site Scraper (Atsogo)
Run the Atsogo scraper to collect all available properties:

```bash
python atsogo_scraper.py
```

### Multi-Site Scraper
Run the multi-site scraper to collect properties from all supported websites:

```bash
python malawi_property_scraper.py
```

### Data Analysis and Visualization

Open the Jupyter notebook `LilongwePropertyAnalysis.ipynb` to explore and visualize the property data. The notebook includes:
- Importing necessary packages (pandas, numpy, matplotlib, seaborn)
- Loading the CSV data
- Splitting the location column into 'city' and 'area'
- Extracting the month name from the date column
- Dropping the original location column
- Exploratory data analysis with summary tables and visualizations

## Output

### Atsogo Scraper Output
Creates `atsogo_properties.csv` with the following columns:
- `title`: Property title/name
- `property_type`: Type of property (Plot, Complete House, Land, etc.)
- `transaction_type`: For Sale or For Rent
- `location`: Property location (city and area)
- `price`: Property price in Malawian Kwacha (MK)
- `area_sqm`: Area in square meters
- `bedrooms`: Number of bedrooms
- `bathrooms`: Number of bathrooms
- `date_posted`: Date when the property was posted
- `description`: Property description (if available)
- **city**: Extracted city from location (added in notebook)
- **area**: Extracted area from location (added in notebook)
- **month**: Month name extracted from date_posted (added in notebook)

### Multi-Site Scraper Output
Creates `malawi_properties.csv` with additional columns:
- `source`: Website source (atsogo, sgw, nyumba24, etc.)
- `url`: Source URL

## Sample Data

Based on the website content, the scrapers will extract data like:

- Plot in Area 41 (LILONGWE, Area 41) - MK 85,000,000.00
- Furnished House (LILONGWE, New Area 43) - MK 2,000.00 (For rent)
- Plot for sale (LILONGWE, Area 46) - MK 115,000,000.00 (2100 sqm)
- Mandala House (Blantyre) - MK 1,500,000 (For rent)
- 308 Hectare Farm (Mangochi) - MK 560,000,000.00 (For sale)

## Supported Websites

### Fully Supported
1. **Atsogo** - Complete property listings with detailed information
2. **SGW** - Homepage property listings
3. **Nyumba24** - Property listings from homepage

### Basic Support (May require additional development)
4. **Knight Frank** - Basic property detection
5. **Reynolds** - Basic property detection
6. **4321 Property** - Basic property detection

## Notes

- The scripts include delays between page requests to be respectful to the servers
- Error handling is included for network issues and parsing problems
- The scripts use realistic User-Agents to avoid being blocked
- Logging is enabled to track the scraping progress
- Each website may have different data availability and structure

## Legal Notice

Please ensure you comply with each website's terms of service and robots.txt file when using these scrapers. These tools are for educational purposes only.

## Dependencies

- `requests`: For making HTTP requests
- `beautifulsoup4`: For parsing HTML content
- `lxml`: XML/HTML parser backend for BeautifulSoup
- `pandas`, `numpy`, `matplotlib`, `seaborn`: For data analysis and visualization in the notebook

## Future Enhancements

- Add support for more property websites
- Implement more sophisticated data extraction for basic support sites
- Add data validation and cleaning
- Create a web interface for the scrapers
- Add support for property images and additional details
