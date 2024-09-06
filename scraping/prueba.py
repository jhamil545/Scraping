import requests
from bs4 import BeautifulSoup

def scrape_news_page(news_url):
    response = requests.get(news_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Encuentra la categoría (ajusta el selector según el HTML real)
        category_element = soup.find('a', class_='tdb-entry-category')
        category = category_element.text.strip() if category_element else 'No category'
        
        # Encuentra el elemento <span> con la imagen
        image_element = soup.find('a', class_='entry-thumb td-thumb-css td-animation-stack-type0-2')
        if image_element:
            image_url = image_element.get('data-img-url')
            if image_url:
                print(f"URL de la imagen: {image_url}")
            else:
                print("No se encontró el atributo 'data-img-url'.")
        else:
            print("No se encontró el elemento de imagen.")
        
        return category
    else:
        print(f"Error al acceder a la noticia: {news_url}")
        return None

def main():
    url = 'https://losandes.com.pe'

    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Encuentra los títulos y URLs
        title_elements = soup.find_all('h3', class_='entry-title')
        date_elements = soup.find_all('time', class_='entry-date')

        for title_element, date_element in zip(title_elements, date_elements):
            title = title_element.a.text.strip()
            date = date_element.text.strip()
            news_url = title_element.a['href'].strip()

            # Extrae la categoría y muestra la URL de la imagen de la noticia
            category = scrape_news_page(news_url)

            print(f"\nTítulo: {title}")
            print(f"Fecha: {date}")
            print(f"Categoría: {category}")
            print(f"URL: {news_url}")
            print("-" * 40)

        print("Extracción exitosa")
    else:
        print(f"Error al realizar el scraping: {response.status_code}")

if __name__ == "__main__":
    main()
