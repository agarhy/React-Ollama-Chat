"""
Database factory for creating database instances
"""
from typing import Dict, Type
from .interface import DatabaseInterface
from .sqlite_db import SQLiteDatabase
from .json_db import JSONDatabase
from .csv_db import CSVDatabase


class DatabaseFactory:
    """Factory for creating database instances"""
    
    _drivers: Dict[str, Type[DatabaseInterface]] = {
        "sqlite": SQLiteDatabase,
        "json": JSONDatabase,
        "csv": CSVDatabase,
    }
    
    @classmethod
    def create(cls, driver: str = "sqlite", **kwargs) -> DatabaseInterface:
        """Create a database instance
        
        Args:
            driver: Database driver type ("sqlite", "json", "csv", "mysql")
            **kwargs: Additional arguments for the database constructor
        
        Returns:
            DatabaseInterface instance
        """
        if driver not in cls._drivers:
            raise ValueError(f"Unsupported database driver: {driver}. Available: {list(cls._drivers.keys())}")
        
        return cls._drivers[driver](**kwargs)
    
    @classmethod
    def register_driver(cls, name: str, driver_class: Type[DatabaseInterface]):
        """Register a new database driver
        
        Args:
            name: Driver name
            driver_class: Driver class implementing DatabaseInterface
        """
        cls._drivers[name] = driver_class
    
    @classmethod
    def list_drivers(cls) -> list:
        """List available database drivers"""
        return list(cls._drivers.keys())
