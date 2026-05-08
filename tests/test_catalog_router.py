from mcp_gateway.catalog.tool_catalog import ToolCatalog
from mcp_gateway.discovery.mock_discovery import MockDiscoveryClient
from mcp_gateway.routing.router_scheduler import RouterScheduler


def test_catalog_lists_demo_tools():
    catalog = ToolCatalog()
    catalog.refresh(MockDiscoveryClient().list_instances())

    tools = catalog.list_tools()
    tool_names = {tool.name for tool in tools}

    assert len(tools) == 3
    assert tool_names == {"knowledge.search", "approval.create_task", "document.generate"}
    assert all(tool.provider_instances for tool in tools)


def test_router_selects_healthy_instance():
    catalog = ToolCatalog()
    catalog.refresh(MockDiscoveryClient().list_instances())
    scheduler = RouterScheduler(catalog)

    route = scheduler.select_route("knowledge.search", tenant_id="tenant-a")

    assert route.selected_instance.instance_id == "knowledge-1"
    assert route.tool_name == "knowledge.search"


def test_router_selects_approval_instance():
    catalog = ToolCatalog()
    catalog.refresh(MockDiscoveryClient().list_instances())
    scheduler = RouterScheduler(catalog)

    route = scheduler.select_route("approval.create_task", tenant_id="tenant-a")

    assert route.selected_instance.instance_id == "approval-1"
    assert route.tool_name == "approval.create_task"
