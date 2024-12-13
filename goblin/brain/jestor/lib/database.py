from typing import Dict, Any, List, Optional, Union
from django.db import connections, connection
from channels.db import database_sync_to_async
import logging
from dataclasses import dataclass
from enum import Enum
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@dataclass
class QueryResult:
    """
    Container for query results that provides a consistent structure for database responses.
    Includes status information and error handling alongside the actual data.
    """
    status: str
    data: List[Dict[str, Any]]
    row_count: int
    error: Optional[str] = None
    
    @property
    def is_success(self) -> bool:
        """Provides a simple way to check if the query executed successfully"""
        return self.status == "success"


class DatabaseType(Enum):
    """
    Defines available database connections using a generalized naming scheme.
    This allows for flexible use of additional databases without prescribing
    specific purposes in the naming.
    """
    DEFAULT = ("default", "Django's primary database connection")
    DB1 = ("additional_database_1", "Additional database connection #1")
    DB2 = ("additional_database_2", "Additional database connection #2")
    DB3 = ("additional_database_3", "Additional database connection #3")

    def __init__(self, value: str, description: str):
        self._value_ = value
        self.description = description
        
    @property
    def connection_name(self) -> str:
        """Returns the actual connection name used in Django settings"""
        return self._value_


class DatabaseManager:
    """
    Manages database operations without storing persistent connections.
    """
    def __init__(self):
        pass  # No need to initialize connections here
    
    @contextmanager
    def get_connection(self, db_type: DatabaseType = DatabaseType.DEFAULT):
        """
        Context manager for safely handling database connections.
        Obtains a fresh connection for the current thread.
        """
        try:
            if db_type.connection_name not in connections.databases:
                raise ValueError(f"No configuration found for database: {db_type.connection_name}")
            
            # Get the connection for the current thread
            connection = connections[db_type.connection_name]
            yield connection
        except Exception as e:
            logger.error(f"Database connection error for {db_type.connection_name}: {str(e)}")
            raise 

    def _initialize_connections(self):
        """
        Set up database connections based on Django settings.
        Logs available connections and any missing configurations.
        """
        # Start with default database
        self._connections[DatabaseType.DEFAULT] = connection
        logger.info(f"Initialized default database connection: {DatabaseType.DEFAULT.connection_name}")
        
        # Initialize additional database connections
        for db_type in DatabaseType:
            if db_type == DatabaseType.DEFAULT:
                continue  # Already handled above
                
            if db_type.connection_name in connections.databases:
                self._connections[db_type] = connections[db_type.connection_name]
                logger.info(f"Initialized additional database connection: {db_type.connection_name}")
            else:
                logger.debug(f"Database configuration not found: {db_type.connection_name}")
    
    def get_available_databases(self) -> Dict[str, str]:
        """
        Returns information about which databases are currently available.
        Useful for debugging and connection verification.
        """
        return {
            db_type.connection_name: {
                'description': db_type.description,
                'available': db_type in self._connections,
                'engine': self._connections[db_type].settings_dict['ENGINE'] 
                         if db_type in self._connections else None
            }
            for db_type in DatabaseType
        }


    async def execute_query(
        self,
        query: str,
        parameters: Optional[Union[list, tuple, dict]] = None,
        db_type: DatabaseType = DatabaseType.DEFAULT
    ) -> QueryResult:
        """
        Execute a query on the specified database connection.
        """
        try:
            if not query.strip().upper().startswith('SELECT'):
                raise ValueError("Only SELECT queries are allowed")
            
            # Wrap the synchronous method with database_sync_to_async
            results = await database_sync_to_async(self._execute_read_query)(
                query, parameters, db_type
            )
            return QueryResult(
                status="success",
                data=results,
                row_count=len(results),
                error=None
            )
        except Exception as e:
            error_msg = f"Query execution error on {db_type.connection_name}: {str(e)}"
            logger.error(error_msg)
            return QueryResult(
                status="error",
                data=[],
                row_count=0,
                error=error_msg
            )

    def _execute_read_query(self, query, parameters=None, db_type=DatabaseType.DEFAULT):
        with self.get_connection(db_type) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, parameters)
                columns = [col[0] for col in cursor.description]
                data = [dict(zip(columns, row)) for row in cursor.fetchall()]
                return data
