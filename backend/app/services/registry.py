from typing import Dict, Type
from app.services.base import BaseService

class ServiceRegistry:
    _instance = None
    _services: Dict[str, BaseService] = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ServiceRegistry()
        return cls._instance

    def register(self, resource_type: str, service_class: Type[BaseService]):
        self._services[resource_type] = service_class()

    def get_service(self, resource_type: str) -> BaseService:
        return self._services.get(resource_type)
