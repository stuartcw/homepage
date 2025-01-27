import requests
from bs4 import BeautifulSoup

URL = 'https://www.python.org/doc/versions/'

def get_latest_doc_url():
    try:
        # Fetch the page
        response = requests.get(URL, timeout=10)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the first link in the list
        list_item = soup.select_one('ul.simple li:first-child a.reference.external')
        
        if not list_item:
            raise ValueError("Could not find version links in the page")
            
        return list_item['href']
    
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    print(get_latest_doc_url())
