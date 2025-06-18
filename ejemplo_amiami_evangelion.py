#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ejemplo de uso de la librería amiami para buscar figuras de Evangelion
Basado en: https://github.com/marvinody/amiami
"""

import amiami



def buscar_figuras_paginado():
    """
    Ejemplo de búsqueda paginada - más eficiente para búsquedas grandes
    """
    print("\n🔍 Búsqueda paginada de figuras de Evangelion...")
    print("=" * 50)
    
    try:
        # Búsqueda paginada - obtiene hasta 30 items por página
        results = amiami.searchPaginated("dragon ball")
        
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


def mostrar_informacion_detallada():
    """
    Muestra información más detallada de los items encontrados
    """
    print("\n🔍 Información detallada de figuras de Evangelion...")
    print("=" * 50)
    
    try:
        results = amiami.searchPaginated("evangelion figure")
        
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

def main():

   
    # Ejecutar ejemplos
    #buscar_figuras_paginado()  # Comenzamos con paginado (más rápido)
    #buscar_personajes_especificos()
    #buscar_con_proxy()
    mostrar_informacion_detallada()
    
  

if __name__ == "__main__":
    main()
