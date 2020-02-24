from setuptools import find_packages, setup

setup(
    name='{{ cookiecutter.module_name }}',
    packages=find_packages(),
    version='0.0.1',
    description='''{{ cookiecutter.description }}''',
    author='{{ cookiecutter.author_name }}',
    license='{% if cookiecutter.open_source_license == 'MIT' %}MIT{% elif cookiecutter.open_source_license == 'BSD-2-Clause' %}BSD-2{% endif %}',
)
