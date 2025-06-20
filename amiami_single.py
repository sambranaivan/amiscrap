#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para actualización individual de productos AmiAmi
Maneja la obtención y actualización de productos específicos usando su gcode
"""

import amiami
from datetime import datetime
from mongo_service import update_single_product


def amiami_detail_to_standard(api_response: dict) -> dict:
    """
    Convierte una respuesta de la API de detalle individual al formato estándar.
    Incluye imágenes de revisión de _embedded.review_images.
    """
    if not api_response.get("item"):
        return {}
    
    item = api_response["item"]
    
    # Parseamos la fecha
    raw_date = item.get("releasedate")
    iso_date = None
    if raw_date:
        raw_date_str = str(raw_date).strip()
        try:
            # Formato ISO completo (YYYY-MM-DD HH:MM:SS o similar)
            if len(raw_date_str) > 10 and ("-" in raw_date_str or "T" in raw_date_str):
                dt = datetime.fromisoformat(raw_date_str.replace("T", " ").split()[0])
                iso_date = dt.date().isoformat()
            # Formato "Mar-2025", "Jan-2024", etc.
            elif "-" in raw_date_str and len(raw_date_str.split("-")) == 2:
                month_str, year_str = raw_date_str.split("-")
                # Mapeo manual de meses en inglés
                month_map = {
                    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
                    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
                }
                if month_str in month_map:
                    year = int(year_str)
                    month = month_map[month_str]
                    dt = datetime(year, month, 1)
                    iso_date = dt.date().isoformat()
                else:
                    # Intentar con strptime como fallback
                    dt = datetime.strptime(raw_date_str, "%b-%Y")
                    iso_date = dt.replace(day=1).date().isoformat()
            # Formato solo año "2025"
            elif raw_date_str.isdigit() and len(raw_date_str) == 4:
                year = int(raw_date_str)
                dt = datetime(year, 1, 1)
                iso_date = dt.date().isoformat()
            # Otros formatos de fecha estándar
            else:
                # Intentar diferentes formatos comunes
                for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]:
                    try:
                        dt = datetime.strptime(raw_date_str, fmt)
                        iso_date = dt.date().isoformat()
                        break
                    except ValueError:
                        continue
        except Exception as e:
            print(f"⚠️  Error parseando fecha '{raw_date}': {e}")
            iso_date = None
    
    # Extraer imágenes de revisión
    review_images = []
    embedded_data = api_response.get("_embedded", {})
    review_images_data = embedded_data.get("review_images", [])
    
    for img in review_images_data:
        review_images.append({
            "image_url": f"https://img.amiami.com{img.get('image_url', '')}",
            "thumb_url": f"https://img.amiami.com{img.get('thumb_url', '')}",
            "alt": img.get("alt", ""),
            "title": img.get("title", "")
        })
    
    # Determinar availability basado en flags
    availability = "Available"
    if item.get("order_closed_flg"):
        if item.get("preorderitem"):
            availability = "Pre-order Closed"
        elif item.get("backorderitem"):
            availability = "Back-order Closed"
        else:
            availability = "Order Closed"
    else:
        if item.get("preorderitem"):
            availability = "Pre-order"
        elif item.get("backorderitem"):
            availability = "Back-order"
        elif item.get("condition_flg"):
            availability = "Pre-owned"
        elif item.get("store_bonus") or item.get("amiami_limited"):
            availability = "Limited"
        elif item.get("saleitem"):
            availability = "On Sale"
    
    return {
        "id": item.get("gcode"),
        "source": "amiami",
        "title": item.get("gname"),
        "url": f"https://www.amiami.com/eng/detail/?gcode={item.get('gcode')}",
        "image_url": f"https://img.amiami.com{item.get('main_image_url', '')}",
        "thumbnail_url": f"https://img.amiami.com{item.get('thumb_url', '')}",
        "sku": item.get("gcode"),
        "jancode": item.get("jancode"),
        "brand": item.get("maker_name"),
        "price": item.get("price"),
        "currency": "JPY",
        "availability": availability,
        "release_date": iso_date,
        "in_stock": bool(item.get("stock")),
        "is_preorder": bool(item.get("preorderitem")),
        "review_images": review_images,
        "spec": item.get("spec"),
        "memo": item.get("memo"),
        "flags": {
            "saleitem": bool(item.get("saleitem")),
            "condition_flg": bool(item.get("condition_flg")),
            "preorderitem": bool(item.get("preorderitem")),
            "backorderitem": bool(item.get("backorderitem")),
            "store_bonus": bool(item.get("store_bonus")),
            "amiami_limited": bool(item.get("amiami_limited")),
            "instock_flg": bool(item.get("instock_flg")),
            "order_closed_flg": bool(item.get("order_closed_flg")),
        },
    }


def actualizar_producto_amiami(gcode: str, proxies=None):
    """
    Actualiza un producto específico de AmiAmi usando su gcode.
    
    Args:
        gcode (str): Código del producto (ej: "FIGURE-172136")
        proxies (dict, optional): Configuración de proxies
    
    Returns:
        dict: Resultado de la operación
    """
    try:
        print(f"🔍 Actualizando producto AmiAmi: {gcode}")
        
        # Obtener datos del producto desde la API
        api_response = amiami.get_item_detail(gcode, proxies=proxies)
        
        if not api_response:
            return {
                "success": False,
                "error": f"No se pudo obtener información del producto {gcode}"
            }
        
        # Convertir a formato estándar
        standardized_product = amiami_detail_to_standard(api_response)
        
        if not standardized_product.get("id"):
            return {
                "success": False,
                "error": f"Error procesando datos del producto {gcode}"
            }
        
        # Guardar en MongoDB
        try:
            mongo_result = update_single_product(
                source="amiami",
                product_id=gcode,
                original_data=api_response,
                standardized_product=standardized_product
            )
            
            print(f"✅ Producto {gcode} actualizado exitosamente:")
            print(f"   - Título: {standardized_product.get('title', 'Sin título')}")
            print(f"   - Precio: {standardized_product.get('price', 'Sin precio')}")
            print(f"   - Disponibilidad: {standardized_product.get('availability', 'Sin info')}")
            print(f"   - Fecha de lanzamiento: {standardized_product.get('release_date', 'Sin fecha')}")
            print(f"   - En stock: {standardized_product.get('in_stock', False)}")
            print(f"   - Es preorden: {standardized_product.get('is_preorder', False)}")
            print(f"   - Imágenes de revisión: {len(standardized_product.get('review_images', []))}")
            print(f"   - Log de scraping ID: {mongo_result['scraping_log_id']}")
            print(f"   - Operación: {mongo_result['product_result']['operation']}")
            
            return {
                "success": True,
                "product": standardized_product,
                "mongo_result": mongo_result
            }
            
        except Exception as e:
            print(f"❌ Error guardando en MongoDB: {e}")
            return {
                "success": False,
                "error": f"Error guardando en MongoDB: {e}",
                "product": standardized_product
            }
        
    except Exception as e:
        print(f"❌ Error actualizando producto {gcode}: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def actualizar_productos_batch(gcodes: list, proxies=None):
    """
    Actualiza múltiples productos de AmiAmi en batch.
    
    Args:
        gcodes (list): Lista de códigos de productos
        proxies (dict, optional): Configuración de proxies
    
    Returns:
        dict: Estadísticas de la operación
    """
    print(f"🚀 Iniciando actualización batch de {len(gcodes)} productos AmiAmi")
    
    exitosos = 0
    errores = 0
    productos_actualizados = []
    errores_detalle = []
    
    for i, gcode in enumerate(gcodes, 1):
        print(f"\n📦 [{i}/{len(gcodes)}] Procesando {gcode}...")
        
        resultado = actualizar_producto_amiami(gcode, proxies=proxies)
        
        if resultado["success"]:
            exitosos += 1
            productos_actualizados.append({
                "gcode": gcode,
                "title": resultado["product"].get("title", "Sin título"),
                "price": resultado["product"].get("price", "Sin precio"),
                "operation": resultado["mongo_result"]["product_result"]["operation"]
            })
        else:
            errores += 1
            errores_detalle.append({
                "gcode": gcode,
                "error": resultado.get("error", "Error desconocido")
            })
    
    print(f"\n📊 Resumen de actualización batch:")
    print(f"   ✅ Exitosos: {exitosos}")
    print(f"   ❌ Errores: {errores}")
    print(f"   📈 Total procesados: {len(gcodes)}")
    
    if errores > 0:
        print(f"\n❌ Productos con errores:")
        for error in errores_detalle:
            print(f"   - {error['gcode']}: {error['error']}")
    
    return {
        "total_procesados": len(gcodes),
        "exitosos": exitosos,
        "errores": errores,
        "productos_actualizados": productos_actualizados,
        "errores_detalle": errores_detalle
    }


def test_date_parsing():
    """Función de prueba para verificar el parseo de fechas"""
    print("🧪 Probando parseo de fechas...")
    
    # Crear datos de prueba simulando respuesta de API
    test_dates = [
        "Mar-2025",
        "Jan-2024", 
        "Dec-2025",
        "2025",
        "2024-03-15",
        "2024-03-15 10:30:00",
        "Invalid-Date",
        "",
        None
    ]
    
    for test_date in test_dates:
        # Simular estructura de respuesta de API
        mock_response = {
            "item": {
                "gcode": "TEST-001",
                "gname": "Test Product",
                "releasedate": test_date,
                "price": 1000
            }
        }
        
        result = amiami_detail_to_standard(mock_response)
        print(f"   '{test_date}' → '{result.get('release_date', 'FAILED')}'")


if __name__ == "__main__":
    print("🧪 Módulo de actualización individual AmiAmi")
    print("=" * 50)
    
    # Probar parseo de fechas primero (descomentado para testing)
    # test_date_parsing()
    
    # Ejemplo de uso individual
    print("\n1️⃣ Ejemplo de actualización individual:")
    resultado = actualizar_producto_amiami("FIGURE-172136")
    
    # Ejemplo de uso batch
    print("\n2️⃣ Ejemplo de actualización batch:")
    # gcodes_ejemplo = ["FIGURE-172136", "FIGURE-172137"]
    # resultado_batch = actualizar_productos_batch(gcodes_ejemplo)
    
    print("\n💡 Para usar:")
    print("   from amiami_single import actualizar_producto_amiami")
    print("   resultado = actualizar_producto_amiami('TU_GCODE_AQUI')") 