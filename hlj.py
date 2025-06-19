import requests
from bs4 import BeautifulSoup
import time
import json
import re
from datetime import datetime

BASE_URL = "https://www.hlj.com/search/?Word=dragonball&page={}&GenreCode2=Action+Figures&GenreCode2=Figures&GenreCode2=Trading+Figures&StockLevel=All+Future+Release"
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
    resp = requests.get(url, headers=headers, timeout=10, verify=False)
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
                # Verificar que sea un Tag (no NavigableString) antes de acceder atributos
                if hasattr(element, 'get'):
                    element_id = element.get("id")
                    if isinstance(element_id, str) and "_" in element_id:
                        # Extraer la parte antes del underscore como posible SKU
                        potential_sku = element_id.split("_")[0]
                        if len(potential_sku) > 3:  # SKUs suelen ser más largos
                            sku = potential_sku
                            break
            except (KeyError, TypeError, AttributeError):
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

def hlj_to_standard(item: dict) -> dict:
    """
    Convierte un producto en formato hlj al formato estándar.
    Formatea release_date como primer día del mes en ISO 8601.
    """
    # Parseamos "Month YYYY" a primer día de mes
    raw_date = item.get("release_date")
    iso_date = None
    if raw_date:
        try:
            dt = datetime.strptime(raw_date, "%B %Y")
            iso_date = dt.replace(day=1).date().isoformat()
        except Exception:
            iso_date = None

    # Aseguramos que la URL e imagen sean absolutas
    image_url = item.get("image")
    if image_url and image_url.startswith("//"):
        image_url = "https:" + image_url

    return {
        "id": item.get("sku"),
        "source": "hlj",
        "title": item.get("title"),
        "url": f"https://www.hlj.com{item.get('url')}",
        "image_url": image_url,
        "sku": item.get("sku"),
        "max_sale_qty": int(item.get("max_sale_qty", 0)),
        #"price": int(item.get("priceNoFormat", 0)),
        "price": int(item.get("sellPriceNoFormat", 0)),
        "currency": item.get("currencyCode"),
        "availability": item.get("availability"),
        "release_date": iso_date,
        "in_stock": bool(item.get("is_in_stock")),
        "flags": {
            "is_on_sale": item.get("is_on_sale"),
            "bargain_sale": item.get("bargain_sale"),
        },
    }

if __name__ == "__main__":
    pages_to_scrape = 1
    productos = scrape_all(pages=pages_to_scrape, delay=2)
    
    # Crear estructura con metadata para datos originales
    original_data = {
        "search_keyword": "evangelion",
        "total_products": len(productos),
        "pages_processed": pages_to_scrape,
        "products": productos
    }
    
    # Guardar datos originales en JSON
    with open("hlj_products.json", "w", encoding="utf-8") as f:
        json.dump(original_data, f, ensure_ascii=False, indent=2)

    # Convertir a formato estándar y guardar en segundo JSON
    productos_estandarizados = [hlj_to_standard(item) for item in productos]
    standard_data = {
        "search_keyword": "evangelion",
        "total_products": len(productos_estandarizados),
        "pages_processed": pages_to_scrape,
        "products": productos_estandarizados
    }
    
    with open("hlj_products_standard.json", "w", encoding="utf-8") as f:
        json.dump(standard_data, f, ensure_ascii=False, indent=2)

    print(f"Total productos scrapeados: {len(productos)}")
    print("Datos originales guardados en hlj_products.json")
    print("Datos estandarizados guardados en hlj_products_standard.json")
