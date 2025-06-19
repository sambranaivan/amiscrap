#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ejemplo de uso de la librería amiami para buscar figuras de Evangelion
Basado en: https://github.com/marvinody/amiami
"""

import amiami
import json
from datetime import datetime



def buscar_figuras_paginado(keyword):
    
    try:
        # Búsqueda paginada - obtiene hasta 30 items por página
        results = amiami.searchPaginated(keyword)
        
        page = 1
        total_items = 0
        
        while results.hasMore and page <= 3:  # Limitamos a 3 páginas para el ejemplo
            print(f"\n📄 Página {page}:")
            print(f"📊 Items en esta página: {len(results.items)}")
            
            for i, item in enumerate(results.items):
                print(f"  {total_items + i + 1}. {item.productName}")
                print(f"     💰 {item.availability}")
            
            total_items += len(results.items)
            
            if results.hasMore and page < 3:
                print("\n⏳ Cargando siguiente página...")
                results.searchNextPage()
                page += 1
            else:
                break
        
        print(f"\n📊 Total de items mostrados: {total_items}")
        
    except Exception as e:
        print(f"❌ Error en la búsqueda paginada: {e}")


def mostrar_informacion_detallada(keyword):
      
    try:
        results = amiami.searchPaginated(keyword)
        
        if results.items:
            # Tomar solo los primeros 3 items para mostrar información detallada
            for i, item in enumerate(results.items[:3]):
               
                print(f"\n📦 Figura #{i+1}:")
                print(f"   📝 Nombre: {item.productName}")
                print(f"   💰 Disponibilidad: {item.availability}")
                print(f"   💰 productURL: {item.productURL}")
                print(f"   💰 flags: {item.flags}")
                
                
                # Intentar obtener más información si está disponible
                if hasattr(item, 'price'):
                    print(f"   💴 Precio: {item.price}")
                if hasattr(item, 'releaseDate'):
                    print(f"   📅 Fecha de lanzamiento: {item.releaseDate}")
                if hasattr(item, 'manufacturer'):
                    print(f"   🏭 Fabricante: {item.manufacturer}")
                if hasattr(item, 'scale'):
                    print(f"   📏 Escala: {item.scale}")
                    
                print("-" * 40)
        else:
            print("❌ No se encontraron figuras")
            
    except Exception as e:
        print(f"❌ Error mostrando información detallada: {e}")

def amiami_to_standard(item: dict) -> dict:
    """
    Convierte un producto en formato amiami al formato estándar.
    Formatea release_date a ISO 8601.
    """
    # Parseamos la fecha de "YYYY-MM-DD hh:mm:ss" a objeto datetime
    raw_date = item.get("releaseDate") or item.get("releasedate")
    iso_date = None
    if raw_date:
        try:
            dt = datetime.fromisoformat(str(raw_date))
            iso_date = dt.isoformat()
        except Exception:
            iso_date = None

    return {
        "id": item.get("gcode"),
        "source": "amiami",
        "title": item.get("productName"),
        "url": item.get("productURL"),
        "image_url": item.get("imageURL"),
        "thumbnail_url": f"https://www.amiami.com{item.get('thumb_url')}",
        "sku": item.get("productCode"),
        "jancode": item.get("jancode"),
        "brand": item.get("maker_name"),
        "price": item.get("price"),
        "currency": "JPY",
        "availability": item.get("availability"),
        "release_date": iso_date,
        "in_stock": bool(item.get("instock_flg")),
        "is_preorder": bool(item.get("preorderitem")),
        "flags": item.get("flags", {}),
    }

def guardar_productos_json(keyword, max_pages=5):
    """
    Busca productos por keyword y guarda los resultados en amiami_products.json
    También guarda una versión estandarizada en amiami_products_standard.json
    
    Args:
        keyword (str): Palabra clave para buscar
        max_pages (int): Número máximo de páginas a procesar (default: 5)
    """
    try:
        print(f"🔍 Buscando productos con keyword: '{keyword}'...")
        
        # Búsqueda paginada
        results = amiami.searchPaginated(keyword)
        
        all_products = []
        standard_products = []
        page = 1
        
        while results.hasMore and page <= max_pages:
            print(f"📄 Procesando página {page}...")
            
            for item in results.items:
                # Obtener todos los atributos del objeto item dinámicamente
                product_data = {}
                
                # Recorrer todos los atributos del objeto
                for attr_name in dir(item):
                    # Filtrar métodos privados y métodos especiales
                    if not attr_name.startswith('_') and not callable(getattr(item, attr_name)):
                        try:
                            attr_value = getattr(item, attr_name)
                            product_data[attr_name] = attr_value
                        except Exception:
                            # Si hay algún error al obtener el atributo, lo omitimos
                            pass
                
                all_products.append(product_data)
                
                # Convertir a formato estándar
                standard_product = amiami_to_standard(product_data)
                standard_products.append(standard_product)
            
            # Intentar cargar la siguiente página
            if results.hasMore and page < max_pages:
                results.searchNextPage()
                page += 1
            else:
                break
        
        # Preparar datos para JSON original
        json_data = {
            "search_keyword": keyword,
            "total_products": len(all_products),
            "pages_processed": page,
            "products": all_products
        }
        
        # Preparar datos para JSON estandarizado
        standard_json_data = {
            "search_keyword": keyword,
            "total_products": len(standard_products),
            "pages_processed": page,
            "products": standard_products
        }
        
        # Guardar en archivo JSON original
        filename = "amiami_products.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        # Guardar en archivo JSON estandarizado
        standard_filename = "amiami_products_standard.json"
        with open(standard_filename, 'w', encoding='utf-8') as f:
            json.dump(standard_json_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Guardados {len(all_products)} productos en '{filename}'")
        print(f"✅ Guardados {len(standard_products)} productos estandarizados en '{standard_filename}'")
        print(f"📊 Total de páginas procesadas: {page}")
        
        return filename, standard_filename
        
    except Exception as e:
        print(f"❌ Error guardando productos en JSON: {e}")
        return None, None

def main():

   
    # Ejecutar ejemplos
    #buscar_figuras_paginado()  # Comenzamos con paginado (más rápido)
    #buscar_personajes_especificos()
    #buscar_con_proxy()
    #mostrar_informacion_detallada("evangelion")
    
    # Nueva función para guardar en JSON
    guardar_productos_json("evangelion",max_pages=1)
    
  

if __name__ == "__main__":
    main()
