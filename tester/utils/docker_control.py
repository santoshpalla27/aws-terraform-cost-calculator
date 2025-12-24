"""
Docker interaction utilities for resilience testing.

Provides safe container restart capabilities for testing platform resilience.
"""
import subprocess
import time
from typing import Optional


class DockerController:
    """Control Docker containers for resilience testing."""
    
    def __init__(self):
        """Initialize Docker controller."""
        self._verify_docker_available()
    
    def _verify_docker_available(self):
        """Verify Docker is available."""
        try:
            result = subprocess.run(
                ['docker', 'version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("Docker is not available")
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            raise RuntimeError(f"Docker is not available: {e}")
    
    def restart_container(self, container_name: str, wait_healthy: bool = True, timeout: int = 30) -> bool:
        """
        Restart a Docker container.
        
        Args:
            container_name: Name of container to restart
            wait_healthy: Wait for container to become healthy
            timeout: Maximum time to wait for health check
            
        Returns:
            True if restart successful
            
        Raises:
            RuntimeError: If restart fails
        """
        print(f"   🔄 Restarting container: {container_name}")
        
        # Restart container
        result = subprocess.run(
            ['docker', 'restart', container_name],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to restart {container_name}: {result.stderr}")
        
        print(f"   ✓ Container restarted: {container_name}")
        
        # Wait for healthy if requested
        if wait_healthy:
            return self.wait_for_healthy(container_name, timeout)
        
        return True
    
    def wait_for_healthy(self, container_name: str, timeout: int = 30) -> bool:
        """
        Wait for container to become healthy.
        
        Args:
            container_name: Name of container
            timeout: Maximum time to wait
            
        Returns:
            True if container becomes healthy
            
        Raises:
            TimeoutError: If container doesn't become healthy
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check container health
            result = subprocess.run(
                ['docker', 'inspect', '--format={{.State.Health.Status}}', container_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                health_status = result.stdout.strip()
                
                if health_status == 'healthy':
                    print(f"   ✓ Container healthy: {container_name}")
                    return True
                
                # If no health check defined, check if running
                if health_status == '<no value>':
                    running_result = subprocess.run(
                        ['docker', 'inspect', '--format={{.State.Running}}', container_name],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if running_result.returncode == 0 and running_result.stdout.strip() == 'true':
                        print(f"   ✓ Container running: {container_name}")
                        return True
            
            time.sleep(1)
        
        raise TimeoutError(f"Container {container_name} did not become healthy within {timeout}s")
    
    def get_container_status(self, container_name: str) -> dict:
        """
        Get container status.
        
        Args:
            container_name: Name of container
            
        Returns:
            Dictionary with status information
        """
        result = subprocess.run(
            ['docker', 'inspect', container_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return {'running': False, 'healthy': False}
        
        import json
        inspect_data = json.loads(result.stdout)[0]
        
        state = inspect_data.get('State', {})
        health = state.get('Health', {})
        
        return {
            'running': state.get('Running', False),
            'healthy': health.get('Status') == 'healthy' if health else state.get('Running', False),
            'status': health.get('Status', 'unknown')
        }
