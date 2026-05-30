from __future__ import annotations

import argparse

from mcp_gateway.examples.nacos_registration import (
    McpServerRegistration,
    NacosMcpServerRegistrar,
    NacosRegistrationConfig,
    knowledge_search_metadata,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Register an example MCP Server to Nacos.")
    parser.add_argument("--endpoint", default="http://127.0.0.1:8848")
    parser.add_argument("--namespace")
    parser.add_argument("--group", default="MCP_SERVER_GROUP")
    parser.add_argument("--service-name", default="mcp-server-knowledge")
    parser.add_argument("--ip", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18081)
    parser.add_argument("--username")
    parser.add_argument("--password")
    parser.add_argument("--deregister", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    registrar = NacosMcpServerRegistrar(
        NacosRegistrationConfig(
            endpoint=args.endpoint,
            namespace=args.namespace,
            group=args.group,
            username=args.username,
            password=args.password,
        )
    )

    if args.deregister:
        result = registrar.deregister_instance(args.service_name, args.ip, args.port)
        print(f"deregister result: {result}")
        return

    result = registrar.register_instance(
        McpServerRegistration(
            service_name=args.service_name,
            ip=args.ip,
            port=args.port,
            metadata=knowledge_search_metadata(),
        )
    )
    print(f"register result: {result}")


if __name__ == "__main__":
    main()
