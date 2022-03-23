import json
import click
from pathlib import Path


BUILD_DIR = Path("deployments/build")


def fix_address_books(build_dir: Path):
    for addr_file in sorted((build_dir / "logs" / "dump").glob("**/addrbook.json")):
        addr_data = json.loads(addr_file.read_text())
        for i in range(len(addr_data["addrs"])):
            *_, post_fix = addr_data["addrs"][i]["addr"]["ip"].split(".")
            addr_data["addrs"][i]["addr"]["ip"] = "127.0.0.1"
            addr_data["addrs"][i]["addr"]["port"] = int(f"2663{int(post_fix)-3}")

        addr_file.write_text(json.dumps(addr_data, indent=4))
        print(f"Updated {addr_file}")


def fix_config_files(build_dir: Path):
    for config_file in sorted((build_dir / "logs" / "dump").glob("**/config.toml")):
        config = config_file.read_text()
        config = config.replace("persistent_peers =", "# persistent_peers =")
        config_file.write_text(config)


@click.command()
@click.option(
    "--build",
    "build_dir",
    type=click.Path(exists=True, dir_okay=True),
    default=BUILD_DIR,
)
def main(build_dir: Path):
    """Main function."""
    build_dir = build_dir.absolute()
    fix_address_books(build_dir)
    fix_config_files(build_dir)


if __name__ == "__main__":
    main()
