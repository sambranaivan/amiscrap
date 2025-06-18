import requests
from bs4 import BeautifulSoup
import time
import json
import re

BASE_URL = "https://www.hlj.com/search/?Word=evangelion&page={}&GenreCode2=Action+Figures&GenreCode2=Figures&GenreCode2=Trading+Figures&StockLevel=All+Future+Release"
LIVE_PRICE_URL = "https://www.hlj.com/search/livePrice/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def extract_csrf_token(soup):
    """Extrae el token CSRF del código JavaScript"""
    # Buscar en todos los scripts de la página
    for script in soup.find_all("script"):
        if script.string:
            script_text = script.string
            # Buscar el patrón 'csrfmiddlewaretoken': 'TOKEN'
            csrf_match = re.search(r"'csrfmiddlewaretoken':\s*'([^']+)'", script_text)
            if csrf_match:
                return csrf_match.group(1)
    return None

def parse_page(page_num):
    url = BASE_URL.format(page_num)
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Extraer token CSRF
    csrf_token = extract_csrf_token(soup)
    
    products = []
    item_codes = []
    
    # Primero extraemos la información básica y los códigos de producto
    for card in soup.select("div.search-widget-block"):
        title_el = card.select_one("p.product-item-name a")
        img_el = card.select_one("a.item-img-wrapper img")
        link_el = card.select_one("a.item-img-wrapper")
        
        # Extraer código de producto del ID o data attributes
        sku = None
        # Buscar en elementos con IDs que contengan códigos de producto
        for element in card.find_all(attrs={"id": True}):
            try:
                element_id = element["id"]
                if isinstance(element_id, str) and "_" in element_id:
                    # Extraer la parte antes del underscore como posible SKU
                    potential_sku = element_id.split("_")[0]
                    if len(potential_sku) > 3:  # SKUs suelen ser más largos
                        sku = potential_sku
                        break
            except (KeyError, TypeError):
                continue
        
        title = title_el.text.strip() if title_el else None
        link = link_el["href"] if link_el else None
        img = img_el["src"] if img_el else None

        if title and sku:
            products.append({
                "sku": sku,
                "title": title,
                "url": link,
                "image": img,
                "price": None,
                "release_date": None
            })
            item_codes.append(sku)

    # Hacer petición a la API livePrice para obtener precios y fechas
    if item_codes and csrf_token:
        try:
            live_price_params = {
                "item_codes": ",".join(item_codes),
                "csrfmiddlewaretoken": csrf_token
            }
            
            price_resp = requests.get(
                LIVE_PRICE_URL,
                params=live_price_params,
                headers=headers,
                timeout=10
            )
            
            if price_resp.status_code == 200:
                price_info = price_resp.json()
                
                # Actualizar productos con información de precios
                for product in products:
                    sku = product["sku"]
                    if sku in price_info:
                        item_data = price_info[sku]
                        # Guardar todos los campos del liveprice response
                        product.update(item_data)
                        # Mantener los campos originales del scraping básico
                        # (title, url, image se mantienen del scraping inicial)
        except Exception as e:
            print(f"Error obteniendo precios: {e}")

    return products

def scrape_all(pages=5, delay=1.0):
    all_products = []
    for p in range(1, pages+1):
        print(f"Scraping página {p}…")
        prods = parse_page(p)
        if not prods:
            break
        all_products.extend(prods)
        time.sleep(delay)  # para no sobrecargar el servidor
    return all_products

if __name__ == "__main__":
    productos = scrape_all(pages=1, delay=2)
    # Guardar en JSON
    with open("hlj_products.json", "w", encoding="utf-8") as f:
        json.dump(productos, f, ensure_ascii=False, indent=2)

    print(f"Total productos scrapeados: {len(productos)}")
    print("Datos guardados en hlj_products.json")
