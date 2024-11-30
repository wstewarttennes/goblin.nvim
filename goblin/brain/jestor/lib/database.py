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
    DB1 = ("additional_db_1", "Additional database connection #1")
    DB2 = ("additional_db_2", "Additional database connection #2")
    DB3 = ("additional_db_3", "Additional database connection #3")

    def __init__(self, value: str, description: str):
        self._value_ = value
        self.description = description
        
    @property
    def connection_name(self) -> str:
        """Returns the actual connection name used in Django settings"""
        return self._value_

class DatabaseManager:
    """
    Manages multiple database connections with a generalized naming scheme.
    Provides a consistent interface for database operations while allowing
    flexible use of additional databases.
    """
    
    def __init__(self):
        self._connections = {}
        self._initialize_connections()
    
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

    @contextmanager
    def get_connection(self, db_type: DatabaseType = DatabaseType.DEFAULT):
        """
        Context manager for safely handling database connections.
        Ensures proper connection handling and error logging.
        """
        try:
            connection = self._connections.get(db_type)
            if not connection:
                raise ValueError(
                    f"No connection found for database: {db_type.connection_name}"
                )
            yield connection
        except Exception as e:
            logger.error(
                f"Database connection error for {db_type.connection_name}: {str(e)}"
            )
            raise

    async def execute_query(
        self,
        query: str,
        parameters: Optional[Union[list, tuple, dict]] = None,
        db_type: DatabaseType = DatabaseType.DEFAULT
    ) -> QueryResult:
        """
        Execute a query on the specified database connection.
        
        Args:
            query: SQL query to execute
            parameters: Query parameters for parameterized queries
            db_type: Which database connection to use
            
        Returns:
            QueryResult containing the results and execution metadata
        """
        try:
            if not query.strip().upper().startswith('SELECT'):
                raise ValueError("Only SELECT queries are allowed")
            
            results = await self._execute_read_query(query, parameters, db_type)
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

    @database_sync_to_async
    def _execute_read_query(self, query, parameters=None, db_type=DatabaseType.DEFAULT):
        with self.get_connection(db_type) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, parameters)
                return cursor.fetchall()
