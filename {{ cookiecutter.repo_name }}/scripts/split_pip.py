#!env python
import json
import sys
import yaml

ACCEPTABLE_FORMATS = ["default", "pip", "pip-yaml", "conda-forge"]

def env_split(conda_env, kind="default"):
    """Given a conda_environment dict, split into pip/nonpip versions

    conda_env: dict
        Python object corresponding to environment.yml"""
    # Cheater way to make deep Copies
    json_copy = json.dumps(conda_env)
    conda_env = json.loads(json_copy)
    pip_env = json.loads(json_copy)

    pipdeps = None
    deplist = conda_env.pop('dependencies')
    conda_forge_list = []

    for k, dep in enumerate(deplist[:]):  # Note: copy list, as we mutate it
        if isinstance(dep, dict):  # nested yaml
            if dep.get('pip', None):
                pipdeps = ["pip", deplist.pop(k)]
        else:
            prefix = 'conda-forge::'
            if dep.startswith(prefix):
                conda_forge_list.append(dep[len(prefix):])
                deplist.remove(dep)

    conda_env['dependencies'] = deplist
    pip_env['dependencies'] = pipdeps
    return conda_env, pip_env, conda_forge_list

def usage():
    print(f"""
Usage:    split_pip.py [{"|".join(ACCEPTABLE_FORMATS)}] path/to/environment.yml
    """)
if __name__ == '__main__':
    if len(sys.argv) != 3:
        usage()
        exit(1)

    kind = sys.argv[1]
    if kind not in ACCEPTABLE_FORMATS:
        usage()
        exit(1)

    with open(sys.argv[2], 'r') as yamlfile:
        conda_env = yaml.safe_load(yamlfile)

    cenv, penv, forgelist = env_split(conda_env)
    if kind == "pip-yaml":
        _ = yaml.dump(penv, sys.stdout, allow_unicode=True, default_flow_style=False)
    elif kind == "pip":
        print("\n".join(penv["dependencies"].pop(-1)["pip"]))
    elif kind == "pip-yaml":
        _ = yaml.dump(penv, sys.stdout, allow_unicode=True, default_flow_style=False)
    elif kind == "default":
        _ = yaml.dump(cenv, sys.stdout, allow_unicode=True, default_flow_style=False)
    elif kind == "conda-forge":
        print("\n".join(forgelist))
    else:
        raise Exception(f"Invalid Kind: {kind}")
