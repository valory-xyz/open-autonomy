# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2025-2026 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Replace agent config values with environment variables using a mapping file."""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict

import click
import yaml
from dotenv import load_dotenv  # type: ignore

CONFIG_REGEX = r"\${.*?:(.*)}"


def find_and_replace(config: list, path: list, new_value: Any) -> list:
    """Find and replace a variable in the agent config.

    Traverses a multi-document YAML config, finds sections containing
    the specified path, and replaces the template value with new_value.
    Handles ${type:value} format — preserves the type prefix.

    :param config: list of YAML documents from safe_load_all.
    :param path: list of keys forming the path to the value.
    :param new_value: the new value to substitute.
    :return: the updated config list.
    """
    matching_section_indices = []
    for i, section in enumerate(config):
        value = section
        try:
            for part in path:
                value = value[part]
            matching_section_indices.append(i)
        except (KeyError, TypeError):
            continue

    if not matching_section_indices:
        raise KeyError(f"Path {path} not found in the config.")

    for section_index in matching_section_indices:
        sub_dic = config[section_index]
        for part in path[:-1]:
            sub_dic = sub_dic[part]

        old_str_value = sub_dic[path[-1]]
        match = re.match(CONFIG_REGEX, str(old_str_value))
        if match is None:
            print(
                f"Warning: value at {path} does not match template pattern: {old_str_value}"
            )
            continue
        old_var_value = match.groups()[0]
        new_str_value = str(old_str_value).replace(old_var_value, new_value)
        sub_dic[path[-1]] = new_str_value

    return config


def load_mapping(mapping_path: Path) -> Dict[str, str]:
    """Load a config mapping file (JSON or YAML)."""
    content = mapping_path.read_text(encoding="utf-8")
    if mapping_path.suffix in (".json",):
        return json.loads(content)
    if mapping_path.suffix in (".yaml", ".yml"):
        return yaml.safe_load(content)
    # Try JSON first, fall back to YAML
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return yaml.safe_load(content)


def run_config_replace(
    mapping: Dict[str, str],
    agent_dir: str = "agent",
    env_file: str = ".env",
) -> None:
    """Replace config values in agent's aea-config.yaml using env vars."""
    if Path(env_file).exists():
        load_dotenv(env_file, override=True)

    config_path = Path(agent_dir, "aea-config.yaml")
    if not config_path.exists():
        print(f"Error: {config_path} not found.")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = list(yaml.safe_load_all(f))

    for path_str, var in mapping.items():
        try:
            new_value = os.getenv(var)
            if new_value is None:
                print(f"Environment variable {var} not found. Skipping...")
                continue
            config = find_and_replace(config, path_str.split("/"), new_value)
        except KeyError:
            print(f"Warning: path {path_str} not found in config. Skipping...")
            continue
        except (ValueError, TypeError) as e:
            print(f"Error replacing {path_str}: {e}")
            raise

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump_all(config, f, sort_keys=False)

    print("Config replacement complete.")


@click.command(name="config-replace")
@click.option(
    "--mapping",
    "mapping_path",
    required=True,
    type=click.Path(exists=True),
    help="Path to config mapping file (JSON or YAML).",
)
@click.option(
    "--env-file",
    default=".env",
    help="Path to .env file (default: .env).",
)
@click.option(
    "--agent-dir",
    default="agent",
    help="Agent directory name (default: agent).",
)
def config_replace(mapping_path: str, env_file: str, agent_dir: str) -> None:
    """Replace agent config values with environment variables."""
    mapping = load_mapping(Path(mapping_path))
    run_config_replace(mapping=mapping, agent_dir=agent_dir, env_file=env_file)
