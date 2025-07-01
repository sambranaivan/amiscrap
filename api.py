from fastapi import FastAPI, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
import uvicorn

# Importar funciones de scraping
from hlj import scrape_all, hlj_to_standard
import amiami
from scrap_amiami import amiami_to_standard

app = FastAPI(
    title="Product Scraper API",
    description="API para buscar productos de figuras en diferentes sitios web",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "message": "Product Scraper API",
        "version": "1.0.0",
        "available_sites": ["hlj", "amiami"],
        "endpoints": {
            "search": "/search?keyword=evangelion&site=hlj&limit=10"
        }
    }

def scrape_hlj_products(keyword: str, limit: int) -> List[Dict[str, Any]]:
    """
    Busca productos en HLJ y los convierte al formato estándar
    """
    try:
        # Calcular número de páginas necesarias (aproximadamente 30 productos por página)
        pages_needed = max(1, (limit + 29) // 30)  # Redondear hacia arriba
        
        # Scraper HLJ con delay reducido para la API
        products = scrape_all(keyword, pages=pages_needed, delay=0.5)
        
        # Convertir al formato estándar
        standard_products = [hlj_to_standard(item) for item in products]
        
        # Limitar el número de resultados
        return standard_products[:limit]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scraping HLJ: {str(e)}")

def scrape_amiami_products(keyword: str, limit: int) -> List[Dict[str, Any]]:
    """
    Busca productos en AmiAmi y los convierte al formato estándar
    """
    try:
        # Usar búsqueda paginada de AmiAmi
        results = amiami.searchPaginated(keyword)
        
        all_products = []
        
        # Recopilar productos hasta alcanzar el límite
        while len(all_products) < limit and results.hasMore:
            for item in results.items:
                if len(all_products) >= limit:
                    break
                    
                # Obtener todos los atributos del objeto item
                product_data = {}
                for attr_name in dir(item):
                    if not attr_name.startswith('_') and not callable(getattr(item, attr_name)):
                        try:
                            attr_value = getattr(item, attr_name)
                            product_data[attr_name] = attr_value
                        except Exception:
                            pass
                
                # Convertir al formato estándar
                standard_product = amiami_to_standard(product_data)
                all_products.append(standard_product)
            
            # Cargar siguiente página si necesitamos más productos
            if len(all_products) < limit and results.hasMore:
                results.searchNextPage()
        
        return all_products[:limit]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scraping AmiAmi: {str(e)}")

@app.get("/search")
async def search_products(
    keyword: str = Query(..., description="Palabra clave para buscar productos"),
    site: str = Query(..., description="Sitio web a buscar (hlj, amiami)"),
    limit: int = Query(default=10, ge=1, le=100, description="Número máximo de productos a retornar (1-100)")
):
    """
    Busca productos en el sitio especificado y retorna los resultados en formato estándar
    
    Args:
        keyword: Palabra clave para la búsqueda (ej: "evangelion", "gundam")
        site: Sitio web donde buscar ("hlj" o "amiami")
        limit: Número máximo de productos a retornar (entre 1 y 100)
    
    Returns:
        JSON con metadata y lista de productos en formato estándar
    """
    
    # Validar sitio
    if site.lower() not in ["hlj", "amiami"]:
        raise HTTPException(
            status_code=400, 
            detail="Site must be 'hlj' or 'amiami'"
        )
    
    start_time = datetime.now()
    
    try:
        if site.lower() == "hlj":
            products = scrape_hlj_products(keyword, limit)
        elif site.lower() == "amiami":
            products = scrape_amiami_products(keyword, limit)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        return {
            "metadata": {
                "search_keyword": keyword,
                "site": site.lower(),
                "requested_limit": limit,
                "actual_count": len(products),
                "timestamp": start_time.isoformat(),
                "processing_time_seconds": round(processing_time, 2)
            },
            "products": products
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/sites")
async def get_available_sites():
    """
    Retorna información sobre los sitios disponibles
    """
    return {
        "available_sites": {
            "hlj": {
                "name": "HobbyLink Japan",
                "url": "https://www.hlj.com",
                "description": "Tienda online de figuras y modelos japoneses"
            },
            "amiami": {
                "name": "AmiAmi",
                "url": "https://www.amiami.com",
                "description": "Tienda online especializada en figuras anime y manga"
            }
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    ) 