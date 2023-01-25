#!env python
import json
import sys
import yaml
from collections import defaultdict


def env_split(conda_env, channel_order):
    """Given a conda_environment dict, and a channel order, split into versions for each channel.

    Returns:

    conda_env: (list)
       remaining setup bits of the environment.yml file
    channel_dict: (dict)
       dict containing the list of dependencies by channel name

        Python object corresponding to environment.yml"""
    # Cheater way to make deep Copies
    json_copy = json.dumps(conda_env)
    conda_env = json.loads(json_copy)
    pip_env = json.loads(json_copy)

    pipdeps = None
    deplist = conda_env.pop('dependencies')
    channel_dict = defaultdict(list)

    for k, dep in enumerate(deplist[:]):  # Note: copy list, as we mutate it
        if isinstance(dep, dict):  # nested yaml
            if dep.get('pip', None):
                channel_dict['pip'] = deplist.pop(k)
        else:
            prefix_check = dep.split('::')
            if len(prefix_check) > 1:
                channel = prefix_check[0]
                if not channel in channel_order:
                    raise Exception(f'the channel {channel} required for {dep} is not specified in a channel-order section of the environment file')
                channel_dict[f'{channel}'].append(prefix_check[1])
                deplist.remove(dep)

    channel_dict['defaults'] = deplist
    conda_env.pop('channel-order')
    return conda_env, channel_dict

def get_channel_order(conda_env):
    """
    Given a conda_environment dict, get the channels from the channel order.
    """
    channel_order = conda_env.get('channel-order')

    if channel_order is None:
        channel_order = ['defaults']
    if not 'defaults' in channel_order:
        channel_order.insert(0, 'defaults')
    channel_order.append('pip')
    return channel_order

def usage():
    print(f"""
Usage:    split_pip.py path/to/environment.yml
    """)
if __name__ == '__main__':
    if len(sys.argv) != 2:
        usage()
        exit(1)

    with open(sys.argv[1], 'r') as yamlfile:
        conda_env = yaml.safe_load(yamlfile)

    #check for acceptable formats
    channel_order = get_channel_order(conda_env)
    with open('.make.channel-order.include', 'w') as f:
        f. write(' '.join(channel_order[:-1])) #exclude pip as a channel here

    cenv, channel_dict = env_split(conda_env, channel_order)

    for kind in channel_order:
        if kind == "pip":
            filename = '.make.pip-requirements.txt'
            with open(filename, 'w') as f:
                f.write("\n".join(channel_dict['pip']['pip']))
        else:
            filename = f'.make.{kind}-environment.txt'
            with open(filename, 'w') as f:
                f.write("\n".join(channel_dict[kind]))
