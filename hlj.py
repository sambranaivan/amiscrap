import requests
from bs4 import BeautifulSoup
import time
import json

BASE_URL = "https://www.hlj.com/search/?Word=evangelion&page={}&GenreCode2=Action+Figures&GenreCode2=Figures&GenreCode2=Trading+Figures&StockLevel=All+Future+Release"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def parse_page(page_num):
    url = BASE_URL.format(page_num)
    resp = requests.get(url, headers=headers, timeout=10, verify=False)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    products = []
    # Selectors actualizados para el formato real de HLJ
    for card in soup.select("div.search-widget-block"):
        title_el = card.select_one("p.product-item-name a")
        price_el = card.select_one("div.price span.bold.stock-left")
        img_el   = card.select_one("a.item-img-wrapper img")
        link_el  = card.select_one("a.item-img-wrapper")

        title = title_el.text.strip() if title_el else None
        link  = link_el["href"] if link_el else None
        # Limpiar el precio de espacios extra, saltos de línea y tabs
        if price_el:
            price_text = price_el.get_text(strip=True)
            # Remover espacios múltiples
            price = ' '.join(price_text.split())
        else:
            price = None
        img   = img_el["src"] if img_el else None

        # Solo agregar productos con título válido
        if title:
            products.append({
                "title": title,
                "price": price,
                "url": link,
                "image": img
            })

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
    productos = scrape_all(pages=2, delay=2)
    # Guardar en JSON
    with open("hlj_products.json", "w", encoding="utf-8") as f:
        json.dump(productos, f, ensure_ascii=False, indent=2)

    print(f"Total productos scrapeados: {len(productos)}")
    print("Datos guardados en hlj_products.json")
