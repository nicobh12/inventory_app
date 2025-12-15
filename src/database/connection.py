"""
Módulo para manejo de conexión a la base de datos SQLite.
"""
import sqlite3
import sys
import logging
from pathlib import Path
from typing import Optional, Any
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)

class DatabaseSignals(QObject):
    """Señales para comunicación con la UI."""
    connection_established = Signal()
    connection_error = Signal(str)
    backup_created = Signal(str)

class DatabaseConnection:
    """Gestor de conexión a la base de datos con señales."""
    
    _instance: Optional['DatabaseConnection'] = None
    _connection: Optional[sqlite3.Connection] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.signals = DatabaseSignals()
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.db_path = self._get_db_path()
            self.setup_logging()
    
    def setup_logging(self):
        """Configura logging para la base de datos."""
        self.db_logger = logging.getLogger('database')
        if not self.db_logger.handlers:
            handler = logging.FileHandler(self.db_path.parent / 'database.log')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.db_logger.addHandler(handler)
            self.db_logger.setLevel(logging.INFO)
    
    def _get_db_path(self) -> Path:
        """Determina la ruta de la base de datos."""
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).parent.parent.parent
        
        data_dir = base_dir / "data"
        data_dir.mkdir(exist_ok=True)
        return data_dir / "inventario.db"
    
    def get_connection(self) -> sqlite3.Connection:
        """Obtiene o crea la conexión a la base de datos."""
        if self._connection is None:
            try:
                # Timeout para evitar bloqueos en operaciones concurrentes
                self._connection = sqlite3.connect(
                    self.db_path,
                    timeout=30,
                    check_same_thread=False
                )
                self._connection.row_factory = sqlite3.Row
                self._connection.execute("PRAGMA foreign_keys = ON")
                self._connection.execute("PRAGMA journal_mode = WAL")  # Mejor rendimiento
                self._connection.execute("PRAGMA synchronous = NORMAL")
                
                logger.info(f"Conexión establecida: {self.db_path}")
                self.signals.connection_established.emit()
                
            except sqlite3.Error as e:
                error_msg = f"Error conectando a la BD: {e}"
                logger.error(error_msg)
                self.signals.connection_error.emit(error_msg)
                raise
        
        return self._connection
    
    def execute_transaction(self, queries: list, params: list = None):
        """
        Ejecuta múltiples queries en una transacción.
        
        Args:
            queries: Lista de queries SQL
            params: Lista de parámetros para cada query (opcional)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            for i, query in enumerate(queries):
                if params and i < len(params):
                    cursor.execute(query, params[i])
                else:
                    cursor.execute(query)
            
            conn.commit()
            return cursor
        
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Error en transacción: {e}")
            self.db_logger.error(f"Transaction failed: {queries}")
            raise
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[dict]:
        """Ejecuta query y retorna una fila como diccionario."""
        conn = self.get_connection()
        cursor = conn.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def fetch_all(self, query: str, params: tuple = ()) -> list[dict]:
        """Ejecuta query y retorna todas las filas como lista de diccionarios."""
        conn = self.get_connection()
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def close_connection(self):
        """Cierra la conexión a la base de datos."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Conexión cerrada")
    
    def backup_database(self, backup_path: Optional[Path] = None) -> Path:
        """Crea un backup de la base de datos."""
        import shutil
        import datetime
        
        if backup_path is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.db_path.parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            backup_path = backup_dir / f"inventario_backup_{timestamp}.db"
        
        # Usar backup API de SQLite para integridad
        conn = self.get_connection()
        backup_conn = sqlite3.connect(backup_path)
        conn.backup(backup_conn)
        backup_conn.close()
        
        logger.info(f"Backup creado en: {backup_path}")
        self.signals.backup_created.emit(str(backup_path))
        return backup_path
    
    def get_database_size(self) -> int:
        """Retorna el tamaño de la base de datos en bytes."""
        if self.db_path.exists():
            return self.db_path.stat().st_size
        return 0


# Instancia global
db = DatabaseConnection()