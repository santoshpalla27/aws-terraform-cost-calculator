"""Usage profile management."""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from .config import settings

logger = logging.getLogger(__name__)


class UsageProfile(BaseModel):
    """Usage profile model."""
    
    profile_name: str
    description: str
    environment: str
    assumptions: List[str]
    defaults: Dict[str, Any]
    scaling: Dict[str, float]
    
    def scale(self, factor: float) -> "UsageProfile":
        """Create a scaled copy of the profile.
        
        Args:
            factor: Scaling factor (e.g., 0.5 for min, 1.5 for max)
            
        Returns:
            Scaled profile
        """
        scaled_defaults = {}
        for key, value in self.defaults.items():
            if isinstance(value, (int, float)):
                scaled_defaults[key] = value * factor
            else:
                scaled_defaults[key] = value
        
        return UsageProfile(
            profile_name=f"{self.profile_name}_scaled_{factor}",
            description=f"{self.description} (scaled {factor}x)",
            environment=self.environment,
            assumptions=self.assumptions + [f"Scaled by factor: {factor}"],
            defaults=scaled_defaults,
            scaling=self.scaling
        )


class ProfileLoader:
    """Loads and manages usage profiles."""
    
    def __init__(self, profiles_dir: str = None):
        """Initialize profile loader.
        
        Args:
            profiles_dir: Directory containing profile YAML files
        """
        self.profiles_dir = Path(profiles_dir or settings.profiles_dir)
        self.profiles: Dict[str, UsageProfile] = {}
        self._load_profiles()
    
    def _load_profiles(self):
        """Load all profiles from directory."""
        if not self.profiles_dir.exists():
            logger.warning(f"Profiles directory not found: {self.profiles_dir}")
            return
        
        for profile_file in self.profiles_dir.glob("*.yaml"):
            try:
                with open(profile_file, 'r') as f:
                    data = yaml.safe_load(f)
                    profile = UsageProfile(**data)
                    self.profiles[profile.profile_name] = profile
                    logger.info(f"Loaded profile: {profile.profile_name}")
            except Exception as e:
                logger.error(f"Failed to load profile {profile_file}: {e}")
    
    def get_profile(self, profile_name: str) -> Optional[UsageProfile]:
        """Get profile by name.
        
        Args:
            profile_name: Profile name
            
        Returns:
            Usage profile or None
        """
        return self.profiles.get(profile_name)
    
    def list_profiles(self) -> List[str]:
        """List available profiles.
        
        Returns:
            List of profile names
        """
        return list(self.profiles.keys())
