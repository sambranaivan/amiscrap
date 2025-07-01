# Product Scraper API

API REST para buscar productos de figuras en diferentes sitios web japoneses (HLJ y AmiAmi).

## Características

- **Múltiples sitios**: Soporte para HobbyLink Japan (HLJ) y AmiAmi
- **Formato estándar**: Todos los productos se retornan en un formato JSON consistente
- **Límite configurable**: Control sobre la cantidad de productos a retornar
- **Documentación automática**: Swagger UI disponible en `/docs`

## Instalación

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

2. Ejecutar la API:
```bash
python api.py
```

O usando uvicorn directamente:
```bash
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

## Uso

### Endpoint principal: `/search`

```
GET /search?keyword={keyword}&site={site}&limit={limit}
```

**Parámetros:**
- `keyword` (requerido): Palabra clave para buscar (ej: "evangelion", "gundam")
- `site` (requerido): Sitio web donde buscar ("hlj" o "amiami")  
- `limit` (opcional): Número máximo de productos a retornar (1-100, default: 10)

### Ejemplos de uso

1. **Buscar figuras de Evangelion en HLJ (10 productos):**
```bash
curl "http://127.0.0.1:8000/search?keyword=evangelion&site=hlj&limit=10"
```

2. **Buscar figuras de Gundam en AmiAmi (5 productos):**
```bash
curl "http://127.0.0.1:8000/search?keyword=gundam&site=amiami&limit=5"
```

3. **Buscar en navegador:**
```
http://127.0.0.1:8000/search?keyword=evangelion&site=hlj&limit=5
```

### Otros endpoints

- `GET /` - Información general de la API
- `GET /sites` - Lista de sitios disponibles
- `GET /docs` - Documentación interactiva (Swagger UI)
- `GET /redoc` - Documentación alternativa (ReDoc)

## Formato de respuesta

```json
{
  "metadata": {
    "search_keyword": "evangelion",
    "site": "hlj",
    "requested_limit": 10,
    "actual_count": 8,
    "timestamp": "2024-01-15T10:30:00.123456",
    "processing_time_seconds": 2.45
  },
  "products": [
    {
      "id": "PRODUCT_ID",
      "source": "hlj",
      "title": "Evangelion Unit-01 Figure",
      "url": "https://www.hlj.com/product/xxx",
      "image_url": "https://img.example.com/image.jpg",
      "sku": "PRODUCT_SKU",
      "price": 5800,
      "currency": "JPY",
      "availability": "Pre-order",
      "release_date": "2024-03-01",
      "in_stock": false,
      "flags": {
        "is_on_sale": false,
        "bargain_sale": false
      }
    }
  ]
}
```

## Campos del formato estándar

- `id`: Identificador único del producto
- `source`: Sitio de origen ("hlj" o "amiami")
- `title`: Nombre del producto
- `url`: URL del producto en el sitio original
- `image_url`: URL de la imagen del producto
- `sku`: Código del producto (SKU)
- `price`: Precio en la moneda especificada
- `currency`: Código de moneda (JPY, USD, etc.)
- `availability`: Estado de disponibilidad
- `release_date`: Fecha de lanzamiento (formato ISO 8601)
- `in_stock`: Booleano indicando si está en stock
- `flags`: Objeto con banderas adicionales (ofertas, etc.)

## Códigos de error

- `400 Bad Request`: Parámetros inválidos (sitio no soportado)
- `500 Internal Server Error`: Error en el scraping o procesamiento

## Desarrollo

La API utiliza las librerías existentes:
- `hlj.py`: Para scraping de HobbyLink Japan
- `amiami.py`: Para scraping de AmiAmi  
- `scrap_amiami.py`: Para conversión al formato estándar de AmiAmi

### Añadir nuevos sitios

Para añadir soporte a nuevos sitios:

1. Crear función de scraping similar a `scrape_hlj_products()` o `scrape_amiami_products()`
2. Crear función de conversión al formato estándar
3. Añadir el sitio a la validación en el endpoint `/search`
4. Actualizar la lista de sitios disponibles

## Notas

- Los scrapers incluyen delays para no sobrecargar los servidores
- El límite máximo de productos por petición es 100
- Los tiempos de respuesta varían según el sitio y número de productos solicitados
- Se recomienda usar la documentación interactiva en `/docs` para probar la API 