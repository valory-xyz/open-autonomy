from pathlib import Path
from aea_swarm.configurations.loader import load_service_config


s, o = load_service_config(Path("packages", "valory", "services", "oracle_hardhat"))
print (s.name)
print (s.agent)
print (s.author)
print (s.aea_version)
print (s.aea_version_specifiers)
print (s.build_entrypoint)


print (s.from_json(s.json).json)