"""
Definición de tablas para el sistema de inventario.
Solo lo necesario según requerimientos, con campo para imágenes.
"""
from .connection import db
import logging

logger = logging.getLogger(__name__)

class DatabaseModels:
    """CREATE TABLE organizados por módulo funcional."""
    
    # ===== TABLAS MAESTRAS =====
    
    @staticmethod
    def create_location_tables():
        """Departamentos y municipios."""
        return [
            """CREATE TABLE IF NOT EXISTS departamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL
            )""",
            
            """CREATE TABLE IF NOT EXISTS municipios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                departamento_id INTEGER NOT NULL,
                FOREIGN KEY (departamento_id) REFERENCES departamentos(id),
                UNIQUE(nombre, departamento_id)
            )"""
        ]
    
    # ===== MÓDULO CLIENTES =====
    
    @staticmethod
    def create_client_tables():
        return [
            """CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                departamento TEXT NOT NULL,
                municipio TEXT NOT NULL,
                nombre_comercial TEXT NOT NULL,
                identificacion TEXT,
                direccion TEXT,
                telefono_fijo TEXT,
                telefono_celular TEXT,
                correo TEXT,
                saldo_credito DECIMAL(15,2) DEFAULT 0,
                activo BOOLEAN DEFAULT 1,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notas TEXT
            )"""
        ]
    
    # ===== MÓDULO PROVEEDORES =====
    
    @staticmethod
    def create_supplier_tables():
        return [
            """CREATE TABLE IF NOT EXISTS proveedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_comercial TEXT NOT NULL,
                tipo TEXT CHECK(tipo IN ('Materia Prima', 'Insumos', 'Servicios', 'Activos', 'No Clasificado')),
                identificacion TEXT,
                departamento TEXT,
                municipio TEXT,
                direccion TEXT,
                telefono_fijo TEXT,
                telefono_celular TEXT,
                correo TEXT,
                activo BOOLEAN DEFAULT 1,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        ]
    
    # ===== MÓDULO PRODUCTOS Y PRESENTACIONES =====
    
    @staticmethod
    def create_product_tables():
        return [
            """CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                imagen_path TEXT,  -- Ruta a la imagen del producto
                precio_min DECIMAL(15,2) NOT NULL,
                precio_max DECIMAL(15,2) NOT NULL,
                activo BOOLEAN DEFAULT 1,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notas TEXT
            )""",
            
            """CREATE TABLE IF NOT EXISTS presentaciones_comerciales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER NOT NULL,
                nombre TEXT NOT NULL,  -- Ej: "Cartón de 24 unidades"
                es_moq BOOLEAN DEFAULT 0,  -- Es la Mínima Unidad de Venta
                unidades_por_moq INTEGER NOT NULL DEFAULT 1,
                activo BOOLEAN DEFAULT 1,
                FOREIGN KEY (producto_id) REFERENCES productos(id)
                    ON DELETE CASCADE
            )""",
            
            """CREATE TABLE IF NOT EXISTS stock_productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER NOT NULL,
                presentacion_id INTEGER NOT NULL,
                cantidad INTEGER DEFAULT 0,
                ubicacion TEXT,
                FOREIGN KEY (producto_id) REFERENCES productos(id),
                FOREIGN KEY (presentacion_id) REFERENCES presentaciones_comerciales(id),
                UNIQUE(producto_id, presentacion_id)
            )"""
        ]
    
    # ===== MÓDULO MATERIA PRIMA =====
    
    @staticmethod
    def create_raw_material_tables():
        return [
            """CREATE TABLE IF NOT EXISTS materia_prima (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,  -- Ej: "Azúcar", "Envase PET 375cc"
                tipo TEXT CHECK(tipo IN ('Azúcar', 'Ácido Cítrico', 'Saborizante', 
                                       'Envase', 'Etiqueta', 'Cinta', 'Tapa', 'Otro')),
                unidad_medida TEXT NOT NULL,  -- "bultos", "kg", "mL", "unidades"
                proveedor_id INTEGER,
                stock_actual DECIMAL(15,4) DEFAULT 0,
                stock_minimo DECIMAL(15,4) DEFAULT 0,
                costo_promedio DECIMAL(15,2) DEFAULT 0,
                imagen_path TEXT,  -- Ruta a la imagen de la materia prima
                activo BOOLEAN DEFAULT 1,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
            )"""
        ]
    
    # ===== MÓDULO COMPRAS =====
    
    @staticmethod
    def create_purchase_tables():
        return [
            """CREATE TABLE IF NOT EXISTS compras_materia_prima (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                materia_prima_id INTEGER NOT NULL,
                proveedor_id INTEGER NOT NULL,
                cantidad DECIMAL(15,4) NOT NULL,
                numero_factura TEXT NOT NULL,
                precio_unitario DECIMAL(15,2) NOT NULL,
                precio_total DECIMAL(15,2) NOT NULL,
                descuento_porcentaje DECIMAL(5,2) DEFAULT 0,
                precio_definitivo DECIMAL(15,2) NOT NULL,
                fecha_compra DATE NOT NULL,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notas TEXT,
                FOREIGN KEY (materia_prima_id) REFERENCES materia_prima(id),
                FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
            )"""
        ]
    
    # ===== MÓDULO VENTAS Y PAGOS =====
    
    @staticmethod
    def create_sales_tables():
        return [
            """CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                numero_factura TEXT NOT NULL,
                fecha_venta DATE NOT NULL,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total DECIMAL(15,2) NOT NULL,
                saldo_pendiente DECIMAL(15,2) DEFAULT 0,
                estado TEXT CHECK(estado IN ('PENDIENTE', 'PARCIAL', 'PAGADA')) DEFAULT 'PENDIENTE',
                notas TEXT,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS ventas_detalle (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                presentacion_id INTEGER NOT NULL,
                cantidad_unidades INTEGER NOT NULL,
                cantidad_moq DECIMAL(10,4) NOT NULL,  -- 1.5, 2.0, etc.
                precio_unitario DECIMAL(15,2) NOT NULL,
                subtotal DECIMAL(15,2) NOT NULL,
                FOREIGN KEY (venta_id) REFERENCES ventas(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (producto_id) REFERENCES productos(id),
                FOREIGN KEY (presentacion_id) REFERENCES presentaciones_comerciales(id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS metodos_pago (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                codigo TEXT UNIQUE NOT NULL  -- 'EFECTIVO', 'NEQUI', 'CAJA_SOCIAL', 'CREDITO'
            )""",
            
            """CREATE TABLE IF NOT EXISTS pagos_venta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id INTEGER NOT NULL,
                metodo_pago_id INTEGER NOT NULL,
                monto DECIMAL(15,2) NOT NULL,
                fecha_pago TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (venta_id) REFERENCES ventas(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (metodo_pago_id) REFERENCES metodos_pago(id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS bolsillos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metodo_pago_id INTEGER NOT NULL,
                saldo_actual DECIMAL(15,2) DEFAULT 0,
                FOREIGN KEY (metodo_pago_id) REFERENCES metodos_pago(id),
                UNIQUE(metodo_pago_id)
            )"""
        ]
    
    # ===== MÓDULO PRODUCCIÓN/EMPACADO =====
    
    @staticmethod
    def create_production_tables():
        return [
            """CREATE TABLE IF NOT EXISTS lotes_produccion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_lote TEXT UNIQUE NOT NULL,
                fecha_produccion DATE NOT NULL,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                producto_id INTEGER NOT NULL,
                presentacion_id INTEGER NOT NULL,
                cantidad_producida INTEGER NOT NULL,
                azucar_utilizada DECIMAL(15,4),
                agua_utilizada DECIMAL(15,4),
                tiempo_produccion_minutos INTEGER,
                uso_colorante BOOLEAN DEFAULT 0,
                rendimiento_esperado DECIMAL(5,2),
                rendimiento_real DECIMAL(5,2),
                imagen_path TEXT,  -- Ruta a imagen del lote o muestra
                notas TEXT,
                FOREIGN KEY (producto_id) REFERENCES productos(id),
                FOREIGN KEY (presentacion_id) REFERENCES presentaciones_comerciales(id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS produccion_detalle (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lote_id INTEGER NOT NULL,
                materia_prima_id INTEGER NOT NULL,
                cantidad_utilizada DECIMAL(15,4) NOT NULL,
                FOREIGN KEY (lote_id) REFERENCES lotes_produccion(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (materia_prima_id) REFERENCES materia_prima(id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS analisis_muestras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lote_id INTEGER NOT NULL,
                fecha_analisis DATE,
                color TEXT,
                textura TEXT,
                sabor TEXT,
                ph DECIMAL(5,2),
                brix DECIMAL(5,2),
                humedad DECIMAL(5,2),
                densidad DECIMAL(5,4),
                viscosidad DECIMAL(5,2),
                observaciones TEXT,
                FOREIGN KEY (lote_id) REFERENCES lotes_produccion(id)
                    ON DELETE CASCADE
            )"""
        ]
    
    # ===== MÓDULO ABONOS =====
    
    @staticmethod
    def create_payment_tables():
        return [
            """CREATE TABLE IF NOT EXISTS abonos_credito (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                fecha_abono DATE NOT NULL,
                monto_total DECIMAL(15,2) NOT NULL,
                notas TEXT,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS abonos_detalle (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                abono_id INTEGER NOT NULL,
                venta_id INTEGER NOT NULL,  -- Factura a la que se aplica
                metodo_pago_id INTEGER NOT NULL,
                monto DECIMAL(15,2) NOT NULL,
                FOREIGN KEY (abono_id) REFERENCES abonos_credito(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (venta_id) REFERENCES ventas(id),
                FOREIGN KEY (metodo_pago_id) REFERENCES metodos_pago(id)
            )"""
        ]
    
    # ===== MÓDULO CONFIGURACIÓN =====
    
    @staticmethod
    def create_config_tables():
        return [
            """CREATE TABLE IF NOT EXISTS configuraciones (
                clave TEXT PRIMARY KEY,
                valor TEXT
            )"""
        ]
    
    # ===== MÉTODO PRINCIPAL =====
    
    def initialize_all_tables(self):
        """
        Ejecuta todos los CREATE TABLE en orden correcto.
        """
        table_groups = [
            # Orden CRÍTICO para foreign keys
            self.create_location_tables(),
            self.create_config_tables(),
            self.create_supplier_tables(),
            self.create_client_tables(),
            self.create_product_tables(),
            self.create_raw_material_tables(),
            [
                # Métodos de pago fijos
                """CREATE TABLE IF NOT EXISTS metodos_pago (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    codigo TEXT UNIQUE NOT NULL
                )"""
            ],
            self.create_purchase_tables(),
            self.create_sales_tables(),
            self.create_production_tables(),
            self.create_payment_tables()
        ]
        
        # Datos iniciales obligatorios
        initial_data = [
            # Métodos de pago (exactamente como lo pidieron)
            """INSERT OR IGNORE INTO metodos_pago (nombre, codigo) VALUES
                ('Efectivo', 'EFECTIVO'),
                ('Consignación a Nequi', 'NEQUI'),
                ('Consignación a Banco Caja Social', 'CAJA_SOCIAL'),
                ('Crédito (fiado)', 'CREDITO')""",
            
            # Bolsillos iniciales (saldo en 0)
            """INSERT OR IGNORE INTO bolsillos (metodo_pago_id, saldo_actual)
               SELECT id, 0 FROM metodos_pago""",
            
            # Configuración básica
            """INSERT OR IGNORE INTO configuraciones (clave, valor) VALUES
                ('empresa_nombre', 'Mi Empresa'),
                ('iva_porcentaje', '0.19'),
                ('rango_precios_habilitado', '1'),
                ('ruta_imagenes', 'data/images')"""
        ]
        
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            logger.info("Creando tablas...")
            
            # Ejecutar CREATE TABLE
            for group in table_groups:
                for query in group:
                    cursor.execute(query)
            
            # Ejecutar datos iniciales
            for query in initial_data:
                cursor.execute(query)
            
            conn.commit()
            logger.info("✅ Base de datos lista")
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            conn.rollback()
            raise


# Instancia global
models = DatabaseModels()