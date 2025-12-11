import networkx as nx
from app.models.terraform import ProjectContext

class DependencyGraph:
    def __init__(self, context: ProjectContext):
        self.context = context
        self.graph = nx.DiGraph()
        self._build_graph()

    def _build_graph(self):
        """
        Builds the DAG based on resource references.
        """
        for address, resource in self.context.resources.items():
            self.graph.add_node(address, data=resource)
            
            # Simple reference detection in values
            # This is a basic implementation. In reality, HCL references are complex.
            # We look for strings that match known resource addresses.
            self._scan_references(address, resource.values)

    def _scan_references(self, source_address: str, data: Any):
        if isinstance(data, dict):
            for key, value in data.items():
                self._scan_references(source_address, value)
        elif isinstance(data, list):
            for item in data:
                self._scan_references(source_address, item)
        elif isinstance(data, str):
            # Check if string contains reference to another resource
            # Very naive string matching for Phase 2 prototype
            for target_address in self.context.resources.keys():
                if target_address in data and target_address != source_address:
                    self.graph.add_edge(source_address, target_address)

    def get_evaluation_order(self):
        """
        Returns resources in topological order (dependencies first).
        """
        try:
            return list(reversed(list(nx.topological_sort(self.graph))))
        except nx.NetworkXUnfeasible:
            # Cycle detected, fallback to arbitrary order or handle error
            return list(self.graph.nodes())
