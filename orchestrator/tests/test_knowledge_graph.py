import pytest
from app.graph_engine.knowledge_graph import KnowledgeGraphEngine, Node, Relationship

kg_engine = KnowledgeGraphEngine()


@pytest.fixture(autouse=True)
def clear_graph():
    kg_engine.clear()


def test_knowledge_graph_multi_hop_traversal():
    # Nodes: Alice (User) -> Payments (Service) -> Billing (Project)
    alice = Node(id="node-user-1", tenant_id="tenant-1", type="User", name="Alice")
    payments_service = Node(id="node-srv-1", tenant_id="tenant-1", type="Service", name="Payments Service")
    billing_project = Node(id="node-proj-1", tenant_id="tenant-1", type="Project", name="Billing Project")

    kg_engine.add_node(alice)
    kg_engine.add_node(payments_service)
    kg_engine.add_node(billing_project)

    # Relationships: Alice OWNS Payments Service; Payments Service DEPENDS_ON Billing Project
    kg_engine.add_relationship(Relationship(source_id="node-user-1", target_id="node-srv-1", relation_type="OWNS"))
    kg_engine.add_relationship(Relationship(source_id="node-srv-1", target_id="node-proj-1", relation_type="DEPENDS_ON"))

    # Single-hop lookup
    owned_services = kg_engine.get_related_entities("node-user-1", relation_type="OWNS")
    assert len(owned_services) == 1
    assert owned_services[0].name == "Payments Service"

    # Multi-hop traversal along ["OWNS", "DEPENDS_ON"]
    end_nodes = kg_engine.multi_hop_search("Alice", ["OWNS", "DEPENDS_ON"])
    assert len(end_nodes) == 1
    assert end_nodes[0].name == "Billing Project"
