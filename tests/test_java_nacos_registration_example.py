from pathlib import Path
import shutil
import subprocess


JAVA_EXAMPLE_DIR = Path("examples/java/nacos-registration")


def test_java_nacos_registration_example_declares_core_contracts():
    registrar = (JAVA_EXAMPLE_DIR / "NacosMcpServerRegistrar.java").read_text(
        encoding="utf-8"
    )
    lifecycle = (JAVA_EXAMPLE_DIR / "McpServerNacosLifecycle.java").read_text(
        encoding="utf-8"
    )
    metadata = (JAVA_EXAMPLE_DIR / "KnowledgeSearchMetadata.java").read_text(
        encoding="utf-8"
    )

    assert "/nacos/v1/ns/instance" in registrar
    assert "/nacos/v1/ns/instance/beat" in registrar
    assert "metadata" in registrar
    assert "mcp" in registrar
    assert "accessToken" in registrar
    assert "AutoCloseable" in lifecycle
    assert "scheduleAtFixedRate" in lifecycle
    assert "deregisterInstance" in lifecycle
    assert "knowledge.search" in metadata
    assert "nacos://mcp-schemas/knowledge.search/1.0.0/input" in metadata


def test_java_nacos_registration_example_compiles_when_jdk_is_available(tmp_path):
    javac = shutil.which("javac")
    if not javac:
        return

    build_dir = tmp_path / "classes"
    build_dir.mkdir()
    sources = [path.name for path in JAVA_EXAMPLE_DIR.glob("*.java")]

    subprocess.run(
        [javac, "-d", str(build_dir), *sources],
        check=True,
        cwd=JAVA_EXAMPLE_DIR,
    )

    assert (
        build_dir
        / "com"
        / "example"
        / "mcp"
        / "nacos"
        / "NacosMcpServerRegistrar.class"
    ).exists()
