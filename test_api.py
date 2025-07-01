import requests
import json
from datetime import datetime

# Configuración de la API
API_BASE_URL = "http://127.0.0.1:8000"

def test_root_endpoint():
    """Prueba el endpoint raíz"""
    print("🔍 Probando endpoint raíz...")
    response = requests.get(f"{API_BASE_URL}/")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Endpoint raíz funcionando")
        print(f"   Version: {data['version']}")
        print(f"   Sitios disponibles: {', '.join(data['available_sites'])}")
        return True
    else:
        print(f"❌ Error en endpoint raíz: {response.status_code}")
        return False

def test_sites_endpoint():
    """Prueba el endpoint de sitios disponibles"""
    print("\n🔍 Probando endpoint de sitios...")
    response = requests.get(f"{API_BASE_URL}/sites")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Endpoint de sitios funcionando")
        for site_key, site_info in data["available_sites"].items():
            print(f"   - {site_key}: {site_info['name']}")
        return True
    else:
        print(f"❌ Error en endpoint de sitios: {response.status_code}")
        return False

def test_search_endpoint(keyword="evangelion", site="amiami", limit=3):
    """Prueba el endpoint de búsqueda"""
    print(f"\n🔍 Probando búsqueda: '{keyword}' en {site} (límite: {limit})...")
    
    params = {
        "keyword": keyword,
        "site": site,
        "limit": limit
    }
    
    try:
        response = requests.get(f"{API_BASE_URL}/search", params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            metadata = data["metadata"]
            products = data["products"]
            
            print("✅ Búsqueda exitosa")
            print(f"   Productos encontrados: {metadata['actual_count']}")
            print(f"   Tiempo de procesamiento: {metadata['processing_time_seconds']}s")
            print(f"   Timestamp: {metadata['timestamp']}")
            
            # Mostrar algunos productos
            print("\n📦 Productos encontrados:")
            for i, product in enumerate(products[:2], 1):  # Mostrar solo los primeros 2
                print(f"   {i}. {product.get('title', 'Sin título')[:60]}...")
                print(f"      💰 Precio: {product.get('price', 'N/A')} {product.get('currency', '')}")
                print(f"      📅 Fecha: {product.get('release_date', 'N/A')}")
                print(f"      🔗 URL: {product.get('url', 'N/A')}")
                print(f"      📊 Disponibilidad: {product.get('availability', 'N/A')}")
                print()
            
            return True
            
        else:
            print(f"❌ Error en búsqueda: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout en la búsqueda (>30s)")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_error_handling():
    """Prueba manejo de errores"""
    print("\n🔍 Probando manejo de errores...")
    
    # Probar sitio inválido
    params = {
        "keyword": "test",
        "site": "sitio_inexistente",
        "limit": 5
    }
    
    response = requests.get(f"{API_BASE_URL}/search", params=params)
    
    if response.status_code == 400:
        print("✅ Manejo de errores funcionando (sitio inválido)")
        error_data = response.json()
        print(f"   Error: {error_data['detail']}")
        return True
    else:
        print(f"❌ Manejo de errores inesperado: {response.status_code}")
        return False

def run_all_tests():
    """Ejecuta todas las pruebas"""
    print("🚀 Iniciando pruebas de la API Product Scraper\n")
    print("=" * 60)
    
    tests = [
        test_root_endpoint,
        test_sites_endpoint,
        lambda: test_search_endpoint("evangelion", "amiami", 2),
        test_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Error inesperado en prueba: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Resumen: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! La API está funcionando correctamente.")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisar configuración.")
    
    print("\n📝 Para usar la API manualmente:")
    print("   http://127.0.0.1:8000/docs - Documentación interactiva")
    print("   http://127.0.0.1:8000/search?keyword=evangelion&site=amiami&limit=5")

if __name__ == "__main__":
    run_all_tests() 