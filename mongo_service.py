#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio para interactuar con MongoDB
Maneja el almacenamiento de datos de scraping y productos estandarizados
"""

from pymongo import MongoClient
from datetime import datetime
import config
import logging
from typing import List, Dict, Any, Optional

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoService:
    """Servicio para manejar operaciones con MongoDB"""
    
    def __init__(self):
        """Inicializar conexión a MongoDB"""
        try:
            self.client = MongoClient(config.mongodburl)
            self.db = self.client[config.database]
            self.products_collection = self.db[config.products_collection]
            self.scrapping_collection = self.db[config.scrapping_collection]
            
            # Crear índice único en la colección de productos por el campo 'id'
            self.products_collection.create_index("id", unique=True)
            
            logger.info("Conexión a MongoDB establecida correctamente")
        except Exception as e:
            logger.error(f"Error conectando a MongoDB: {e}")
            raise

    def save_scraping_log(self, 
                         source: str, 
                         keyword: str, 
                         total_products: int, 
                         pages_processed: int, 
                         products_data: List[Dict[str, Any]]) -> str:
        """
        Guarda un log completo del scraping en la colección de scrapping.
        
        Args:
            source: Fuente del scraping ('amiami', 'hlj', etc.)
            keyword: Palabra clave utilizada en la búsqueda
            total_products: Total de productos encontrados
            pages_processed: Número de páginas procesadas
            products_data: Lista completa de productos scraped (formato original)
        
        Returns:
            str: ID del documento insertado
        """
        try:
            scraping_log = {
                "source": source,
                "search_keyword": keyword,
                "total_products": total_products,
                "pages_processed": pages_processed,
                "timestamp": datetime.now(),
                "products_data": products_data
            }
            
            result = self.scrapping_collection.insert_one(scraping_log)
            logger.info(f"Log de scraping guardado para {source} - {keyword}: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error guardando log de scraping: {e}")
            raise

    def upsert_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inserta o actualiza un producto en la colección de productos.
        Usa el campo 'id' como clave única.
        
        Args:
            product: Producto en formato estandarizado
        
        Returns:
            dict: Resultado de la operación con información de si fue inserción o actualización
        """
        try:
            if not product.get('id'):
                raise ValueError("El producto debe tener un campo 'id'")
            
            # Añadir timestamp de actualización
            product['updated_at'] = datetime.now()
            
            # Si es la primera vez que se inserta, añadir created_at
            existing_product = self.products_collection.find_one({"id": product['id']})
            
            if not existing_product:
                product['created_at'] = datetime.now()
                operation_type = "inserted"
            else:
                # Mantener el created_at original
                product['created_at'] = existing_product.get('created_at', datetime.now())
                operation_type = "updated"
            
            # Realizar upsert
            result = self.products_collection.replace_one(
                {"id": product['id']}, 
                product, 
                upsert=True
            )
            
            logger.info(f"Producto {operation_type}: {product['id']} - {product.get('title', 'Sin título')}")
            
            return {
                "product_id": product['id'],
                "operation": operation_type,
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "upserted_id": result.upserted_id
            }
            
        except Exception as e:
            logger.error(f"Error en upsert de producto {product.get('id', 'ID desconocido')}: {e}")
            raise

    def upsert_products_batch(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Inserta o actualiza múltiples productos de manera eficiente.
        
        Args:
            products: Lista de productos en formato estandarizado
        
        Returns:
            dict: Estadísticas de la operación
        """
        try:
            inserted_count = 0
            updated_count = 0
            errors = []
            
            for product in products:
                try:
                    result = self.upsert_product(product)
                    if result['operation'] == 'inserted':
                        inserted_count += 1
                    else:
                        updated_count += 1
                except Exception as e:
                    errors.append({
                        "product_id": product.get('id', 'Desconocido'),
                        "error": str(e)
                    })
            
            logger.info(f"Batch upsert completado: {inserted_count} insertados, {updated_count} actualizados, {len(errors)} errores")
            
            return {
                "total_processed": len(products),
                "inserted_count": inserted_count,
                "updated_count": updated_count,
                "error_count": len(errors),
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Error en batch upsert: {e}")
            raise

    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un producto por su ID.
        
        Args:
            product_id: ID del producto
        
        Returns:
            dict: Producto encontrado o None
        """
        try:
            return self.products_collection.find_one({"id": product_id})
        except Exception as e:
            logger.error(f"Error obteniendo producto {product_id}: {e}")
            return None

    def get_scraping_logs(self, 
                         source: Optional[str] = None, 
                         limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene logs de scraping, opcionalmente filtrados por fuente.
        
        Args:
            source: Fuente a filtrar (opcional)
            limit: Número máximo de logs a retornar
        
        Returns:
            list: Lista de logs de scraping
        """
        try:
            query = {}
            if source:
                query["source"] = source
            
            return list(self.scrapping_collection.find(query)
                       .sort("timestamp", -1)
                       .limit(limit))
        except Exception as e:
            logger.error(f"Error obteniendo logs de scraping: {e}")
            return []

    def get_products_by_source(self, 
                              source: str, 
                              limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtiene productos por fuente.
        
        Args:
            source: Fuente de los productos
            limit: Número máximo de productos a retornar
        
        Returns:
            list: Lista de productos
        """
        try:
            return list(self.products_collection.find({"source": source})
                       .sort("updated_at", -1)
                       .limit(limit))
        except Exception as e:
            logger.error(f"Error obteniendo productos de {source}: {e}")
            return []

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de las colecciones.
        
        Returns:
            dict: Estadísticas de las colecciones
        """
        try:
            products_count = self.products_collection.count_documents({})
            scraping_logs_count = self.scrapping_collection.count_documents({})
            
            # Estadísticas por fuente
            pipeline = [
                {"$group": {"_id": "$source", "count": {"$sum": 1}}}
            ]
            products_by_source = list(self.products_collection.aggregate(pipeline))
            scraping_by_source = list(self.scrapping_collection.aggregate(pipeline))
            
            return {
                "products": {
                    "total": products_count,
                    "by_source": products_by_source
                },
                "scraping_logs": {
                    "total": scraping_logs_count,
                    "by_source": scraping_by_source
                }
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}

    def close_connection(self):
        """Cierra la conexión a MongoDB"""
        try:
            self.client.close()
            logger.info("Conexión a MongoDB cerrada")
        except Exception as e:
            logger.error(f"Error cerrando conexión: {e}")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close_connection()


# Funciones de conveniencia para usar sin instanciar la clase
def save_scraping_data(source: str, 
                      keyword: str, 
                      original_data: List[Dict[str, Any]], 
                      standardized_products: List[Dict[str, Any]],
                      pages_processed: int = 1) -> Dict[str, Any]:
    """
    Función de conveniencia para guardar datos de scraping completos.
    
    Args:
        source: Fuente del scraping
        keyword: Palabra clave de búsqueda
        original_data: Datos originales del scraping
        standardized_products: Productos en formato estandarizado
        pages_processed: Número de páginas procesadas
    
    Returns:
        dict: Resultado de las operaciones
    """
    with MongoService() as mongo:
        # Guardar log de scraping
        scraping_id = mongo.save_scraping_log(
            source=source,
            keyword=keyword,
            total_products=len(original_data),
            pages_processed=pages_processed,
            products_data=original_data
        )
        
        # Guardar productos estandarizados
        batch_result = mongo.upsert_products_batch(standardized_products)
        
        return {
            "scraping_log_id": scraping_id,
            "products_result": batch_result
        } 