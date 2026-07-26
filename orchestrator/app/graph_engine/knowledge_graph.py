from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class Node(BaseModel):
    id: str
    tenant_id: str
    type: str  # "User", "Project", "Service", "Repository", "Document"
    name: str
    properties: Dict[str, Any] = {}


class Relationship(BaseModel):
    source_id: str
    target_id: str
    relation_type: str  # "OWNS", "DEPENDS_ON", "CONTRIBUTES_TO", "AUTHORED"


class KnowledgeGraphEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KnowledgeGraphEngine, cls).__new__(cls)
            cls._instance.nodes = {}
            cls._instance.relationships = []
        return cls._instance

    def add_node(self, node: Node):
        self.nodes[node.id] = node

    def add_relationship(self, rel: Relationship):
        self.relationships.append(rel)

    def clear(self):
        self.nodes = {}
        self.relationships = []

    def get_related_entities(self, entity_id: str, relation_type: Optional[str] = None) -> List[Node]:
        results = []
        for rel in self.relationships:
            if rel.source_id == entity_id:
                if relation_type is None or rel.relation_type == relation_type:
                    target_node = self.nodes.get(rel.target_id)
                    if target_node:
                        results.append(target_node)
        return results

    def multi_hop_search(self, start_entity_name: str, target_relation_chain: List[str]) -> List[Node]:
        """Perform a multi-hop traversal along a relation chain (e.g. ['OWNS', 'DEPENDS_ON'])."""
        start_node = None
        for n in self.nodes.values():
            if n.name.lower() == start_entity_name.lower():
                start_node = n
                break

        if not start_node:
            return []

        current_nodes = [start_node]
        for rel_type in target_relation_chain:
            next_nodes = []
            for curr in current_nodes:
                related = self.get_related_entities(curr.id, relation_type=rel_type)
                next_nodes.extend(related)
            current_nodes = next_nodes

        return current_nodes
