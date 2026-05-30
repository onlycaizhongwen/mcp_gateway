from __future__ import annotations

import argparse

from mcp_gateway.examples.nacos_schema_config import NacosSchemaConfig, NacosSchemaPublisher


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish sample MCP tool schemas to Nacos Config")
    parser.add_argument("--endpoint", default="http://127.0.0.1:8848")
    parser.add_argument("--namespace")
    parser.add_argument("--group", default="MCP_SCHEMA_GROUP")
    parser.add_argument("--username")
    parser.add_argument("--password")
    parser.add_argument("--timeout-seconds", type=float, default=3)
    args = parser.parse_args()

    publisher = NacosSchemaPublisher(
        NacosSchemaConfig(
            endpoint=args.endpoint,
            namespace=args.namespace,
            group=args.group,
            username=args.username,
            password=args.password,
            timeout_seconds=args.timeout_seconds,
        )
    )
    data_ids = publisher.publish_sample_schemas()
    for data_id in data_ids:
        print(f"published {data_id}")


if __name__ == "__main__":
    main()
