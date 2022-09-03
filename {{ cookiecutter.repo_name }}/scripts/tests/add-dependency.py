import sys
import yaml


if __name__ == "__main__":
    assert len(sys.argv[1:]) == 1
    dependency_new = sys.argv[1]

    with open("environment.yml", "rt", encoding="utf-8") as file_env:
        env = yaml.safe_load(file_env)
    env["dependencies"].append(dependency_new)
    with open("environment.yml", "wt", encoding="utf-8") as file_env:
        yaml.safe_dump(env, file_env)
