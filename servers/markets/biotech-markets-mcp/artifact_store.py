"""
Simple in-process artifact store for biotech company dossiers.

This module provides a minimal artifact store for storing and retrieving
dossier artifacts. It's designed to be simple and in-process (no external
dependencies like databases).
"""

import uuid
from typing import Dict, Optional, Any
from datetime import datetime


class ArtifactStore:
    """
    Simple in-process artifact store.
    
    Stores artifacts in memory with unique IDs. In a production system,
    this could be replaced with a database or distributed cache.
    """
    
    def __init__(self):
        """Initialize an empty artifact store."""
        self._artifacts: Dict[str, Dict[str, Any]] = {}
    
    def store(self, artifact: Dict[str, Any], artifact_type: str = "dossier") -> str:
        """
        Store an artifact and return its ID.
        
        Args:
            artifact: Artifact data to store
            artifact_type: Type of artifact (default: "dossier")
        
        Returns:
            Unique artifact ID
        """
        artifact_id = str(uuid.uuid4())
        self._artifacts[artifact_id] = {
            "id": artifact_id,
            "type": artifact_type,
            "data": artifact,
            "stored_at": datetime.utcnow().isoformat() + "Z"
        }
        return artifact_id
    
    def get(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an artifact by ID.
        
        Args:
            artifact_id: Artifact ID
        
        Returns:
            Artifact data or None if not found
        """
        artifact_entry = self._artifacts.get(artifact_id)
        if artifact_entry:
            return artifact_entry["data"]
        return None
    
    def delete(self, artifact_id: str) -> bool:
        """
        Delete an artifact by ID.
        
        Args:
            artifact_id: Artifact ID
        
        Returns:
            True if deleted, False if not found
        """
        if artifact_id in self._artifacts:
            del self._artifacts[artifact_id]
            return True
        return False
    
    def list_artifacts(self, artifact_type: Optional[str] = None) -> list:
        """
        List all artifacts, optionally filtered by type.
        
        Args:
            artifact_type: Optional type filter
        
        Returns:
            List of artifact metadata dictionaries
        """
        artifacts = []
        for artifact_id, entry in self._artifacts.items():
            if artifact_type is None or entry["type"] == artifact_type:
                artifacts.append({
                    "id": entry["id"],
                    "type": entry["type"],
                    "stored_at": entry["stored_at"]
                })
        return artifacts


# Global artifact store instance
_artifact_store = ArtifactStore()


def get_artifact_store() -> ArtifactStore:
    """
    Get the global artifact store instance.
    
    Returns:
        Global ArtifactStore instance (singleton)
    """
    return _artifact_store
