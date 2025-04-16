"""
Schema management utilities for Notion objects.
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory"""
    # Assuming this file is in src/schemas/schema_manager.py
    return Path(__file__).parent.parent.parent

def get_data_dir() -> Path:
    """Get the data directory path, creating it if it doesn't exist"""
    data_dir = get_project_root() / "data" / "schemas"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

class SchemaManager:
    """Manages Notion object schemas"""
    
    def __init__(self, config_name: str = "default"):
        """Initialize schema manager for a specific configuration
        
        Args:
            config_name: Name of the configuration (e.g., 'personal', 'work', 'test')
        """
        self.config_name = config_name
        self.schema_dir = get_data_dir() / config_name
        self.schema_dir.mkdir(parents=True, exist_ok=True)
    
    def get_schema_path(self, schema_type: str) -> Path:
        """Get the path for a schema file"""
        return self.schema_dir / f"{schema_type}.json"
    
    def save_schema(self, schema_type: str, schema: Dict[str, Any]) -> None:
        """Save a schema definition to file"""
        try:
            schema_path = self.get_schema_path(schema_type)
            with open(schema_path, 'w') as f:
                json.dump(schema, f, indent=2)
            logger.info(f"Saved schema for {schema_type} (config: {self.config_name})")
        except Exception as e:
            logger.error(f"Error saving schema for {schema_type}: {e}")
            raise
    
    def load_schema(self, schema_type: str) -> Optional[Dict[str, Any]]:
        """Load a schema definition from file"""
        try:
            schema_path = self.get_schema_path(schema_type)
            if not schema_path.exists():
                logger.warning(f"No schema file found for {schema_type} (config: {self.config_name})")
                return None
            
            with open(schema_path) as f:
                schema = json.load(f)
            logger.info(f"Loaded schema for {schema_type} (config: {self.config_name})")
            return schema
        except Exception as e:
            logger.error(f"Error loading schema for {schema_type}: {e}")
            return None
    
    def list_schemas(self) -> List[str]:
        """List all available schemas for the configuration"""
        try:
            return [f.stem for f in self.schema_dir.glob("*.json")]
        except Exception as e:
            logger.error(f"Error listing schemas: {e}")
            return []
    
    def extract_database_schema(self, database: Dict[str, Any]) -> Dict[str, Any]:
        """Extract schema information from a Notion database response"""
        schema = {
            "id": database["id"],
            "title": database["title"][0]["plain_text"] if database.get("title") else "",
            "properties": {}
        }
        
        # Extract property configurations
        for prop_name, prop_config in database.get("properties", {}).items():
            schema["properties"][prop_name] = {
                "type": prop_config["type"],
                "config": prop_config[prop_config["type"]] if prop_config["type"] in prop_config else {}
            }
        
        return schema
    
    @staticmethod
    def list_configs() -> List[str]:
        """List all available schema configurations"""
        try:
            schema_root = get_data_dir()
            return [d.name for d in schema_root.iterdir() if d.is_dir()]
        except Exception as e:
            logger.error(f"Error listing configurations: {e}")
            return [] 