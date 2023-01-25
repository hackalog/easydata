import sys
import yaml


if __name__ == "__main__":
    channel_order = ['defaults', 'pytorch']
    dependency_new = "pytorch::cpuonly"

    with open("environment.yml", "rt", encoding="utf-8") as file_env:
        env = yaml.safe_load(file_env)
    env["dependencies"].append(dependency_new)
    env["channel_order"] = channel_order
    with open("environment.yml", "wt", encoding="utf-8") as file_env:
        yaml.safe_dump(env, file_env)
