"""
MySQL configuration for mem0 memory storage
"""

from typing import Optional
from pydantic import BaseModel, Field


class MySQLConfig(BaseModel):
    """Configuration for MySQL memory storage"""
    
    host: str = Field(default="localhost", description="MySQL server host")
    port: int = Field(default=3306, description="MySQL server port")
    user: str = Field(default="root", description="MySQL username")
    password: str = Field(default="", description="MySQL password")
    database: str = Field(default="mem0", description="MySQL database name")
    charset: str = Field(default="utf8mb4", description="MySQL charset")
    collation: str = Field(default="utf8mb4_unicode_ci", description="MySQL collation")
    autocommit: bool = Field(default=True, description="Enable autocommit")
    
    # Connection pool settings
    pool_name: Optional[str] = Field(default=None, description="Connection pool name")
    pool_size: int = Field(default=5, description="Connection pool size")
    pool_reset_session: bool = Field(default=True, description="Reset session on pool connection")
    
    # SSL settings
    ssl_disabled: bool = Field(default=True, description="Disable SSL connection")
    ssl_ca: Optional[str] = Field(default=None, description="SSL CA certificate path")
    ssl_cert: Optional[str] = Field(default=None, description="SSL certificate path")
    ssl_key: Optional[str] = Field(default=None, description="SSL private key path")
    
    class Config:
        extra = "allow"  # Allow additional configuration options
    
    @classmethod
    def for_xiaozhi_server(cls, host: str = "localhost", password: str = "123456"):
        """
        Create MySQL config for xiaozhi-esp32-server setup
        
        Args:
            host: MySQL host (default: localhost)
            password: MySQL password (default: 123456)
        """
        return cls(
            host=host,
            port=3306,
            user="root",
            password=password,
            database="xiaozhi_esp32_server",
        )
    
    @classmethod
    def for_docker(cls, host: str = "localhost", port: int = 3306):
        """
        Create MySQL config for Docker setup
        
        Args:
            host: MySQL host (default: localhost for host machine access)
            port: MySQL port (default: 3306)
        """
        return cls(
            host=host,
            port=port,
            user="root",
            password="123456",
            database="xiaozhi_esp32_server",
        )
    
    def to_connection_dict(self) -> dict:
        """Convert to dictionary for mysql.connector.connect()"""
        config = {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "database": self.database,
            "charset": self.charset,
            "collation": self.collation,
            "autocommit": self.autocommit,
        }
        
        # Add SSL settings if not disabled
        if not self.ssl_disabled:
            ssl_config = {}
            if self.ssl_ca:
                ssl_config["ca"] = self.ssl_ca
            if self.ssl_cert:
                ssl_config["cert"] = self.ssl_cert
            if self.ssl_key:
                ssl_config["key"] = self.ssl_key
            
            if ssl_config:
                config["ssl"] = ssl_config
        
        # Add pool settings if pool_name is specified
        if self.pool_name:
            config.update({
                "pool_name": self.pool_name,
                "pool_size": self.pool_size,
                "pool_reset_session": self.pool_reset_session,
            })
        
        return config