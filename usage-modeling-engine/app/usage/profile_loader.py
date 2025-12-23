"""
Profile loader for usage profiles.
"""
import yaml
from pathlib import Path
from typing import Dict, Any
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ProfileLoader:
    """Loads and manages usage profiles."""
    
    def __init__(self, profiles_path: Path):
        """
        Initialize profile loader.
        
        Args:
            profiles_path: Path to profiles directory
        """
        self.profiles_path = profiles_path
        self.profiles: Dict[str, Dict[str, Any]] = {}
    
    def load_profiles(self) -> None:
        """Load all profiles from profiles directory."""
        if not self.profiles_path.exists():
            logger.error(f"Profiles directory not found: {self.profiles_path}")
            raise FileNotFoundError(f"Profiles directory not found: {self.profiles_path}")
        
        # Load all YAML files
        for profile_file in self.profiles_path.glob("*.yaml"):
            try:
                profile_name = profile_file.stem
                with open(profile_file, 'r') as f:
                    profile_data = yaml.safe_load(f)
                
                # Validate profile
                if not self._validate_profile(profile_data):
                    logger.warning(f"Invalid profile: {profile_name}, skipping")
                    continue
                
                self.profiles[profile_name] = profile_data
                logger.info(f"Loaded profile: {profile_name} (version: {profile_data.get('version', 'unknown')})")
                
            except Exception as e:
                logger.error(f"Failed to load profile {profile_file}: {e}")
        
        if not self.profiles:
            logger.warning("No valid profiles loaded")
        else:
            logger.info(f"Loaded {len(self.profiles)} profiles: {list(self.profiles.keys())}")
    
    def get_profile(self, profile_name: str) -> Dict[str, Any]:
        """
        Get a specific profile.
        
        Args:
            profile_name: Name of profile to get
            
        Returns:
            Profile data
            
        Raises:
            ValueError: If profile not found
        """
        if profile_name not in self.profiles:
            available = list(self.profiles.keys())
            raise ValueError(f"Profile '{profile_name}' not found. Available: {available}")
        
        return self.profiles[profile_name]
    
    def list_profiles(self) -> list[str]:
        """Get list of available profile names."""
        return list(self.profiles.keys())
    
    def _validate_profile(self, profile_data: Dict[str, Any]) -> bool:
        """
        Validate profile structure.
        
        Args:
            profile_data: Profile data to validate
            
        Returns:
            True if valid
        """
        required_fields = ['version', 'name', 'description']
        
        for field in required_fields:
            if field not in profile_data:
                logger.error(f"Profile missing required field: {field}")
                return False
        
        return True
    
    def reload_profiles(self) -> None:
        """Reload all profiles (hot-reload)."""
        logger.info("Reloading profiles...")
        self.profiles.clear()
        self.load_profiles()
