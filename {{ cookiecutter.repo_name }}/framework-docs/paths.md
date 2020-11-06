## Specifying paths in Easydata

As hardcoded paths are a notorious source of reproducibility issues, Easydata attempts to help avoid path-related issues by introducing a mechanism called `paths`.

```
>>> from {{ cookiecutter.module_name }} import paths
```

The goal of the `paths` mechanism is to help ensure that **hardcoded path data is never checked-in** to the git repository.

In an Easydata project, paths are recorded in `catalog/config.ini`.  This is a standard `configparser`-format _ini_ file (in [ExtendedInterpolation] format).  The paths specified in this file are used throughout Easydata to specify the standard locations of data artifacts.

[ExtendedInterpolation]: https://docs.python.org/3/library/configparser.html#configparser.ExtendedInterpolation

Because [ExtendedInterpolation] format is used, paths may refer to each other without the need to specify absolute path names.  The default paths, for example, are all relative to `project_path`:

```
[Paths]
data_path = ${project_path}/data
raw_data_path = ${data_path}/raw
interim_data_path = ${data_path}/interim
processed_data_path = ${data_path}/processed
project_path = ${catalog_path}/..
```

Note that, for chicken-and-egg reasons, `catalog_path` (the location of the `config.ini` file used to specify the paths) is **not specified** in this file. It is set upon module instantiation (when ` {{ cookiecutter.module_name }}` is imported) and is write-protected:

```
>>> paths['catalog_path']
PosixPath('/tmpx/project/catalog')
>>> paths['catalog_path'] = '/tmp'
Traceback (most recent call last):
 ...
AttributeError: catalog_path is write-protected
```

### Accessing `paths` from Python

Within Python, `paths` appears to be a dictionary of standard path locations.  For instance, if your Easydata project lives in the `/path/to/repo` directory:

```python
>>>  {{ cookiecutter.module_name }}.path['project_path']
/paths/to/repo
>>> type(paths['project_path'])
pathlib.PosixPath
```

Notice that paths are automatically resolved to absolute filenames (in [pathlib] format) when accessed.

```python
>>> for name, location in paths.items():
>>>     print(f"{name}: {location}")
data_path: /path/to/repo/ReproAllTheThings/data
raw_data_path: /path/to/repo/ReproAllTheThings/data/raw
interim_data_path: /path/to/repo/ReproAllTheThings/data/interim
processed_data_path: /path/to/repo/ReproAllTheThings/data/processed
project_path: /path/to/repo/ReproAllTheThings
```
[pathlib]: https://docs.python.org/3/library/pathlib.html

Even though absolute paths are returned from the dictionary, the relative nature of the paths is preserved when these paths are modified.


### Modifying paths

Recall that one of the Easydata design goals is to ensure that hardcoded paths should not be checked into your git repository. To this end, paths should **never be set from within notebooks or source code that is checked-in** to git. If you wish to modify a path on your local system, edit `config.ini` directly, or use python from the command line, as shown show below:

```bash
>>> python -c "import  {{ cookiecutter.module_name }};  {{ cookiecutter.module_name }}.paths['project_path'] = /alternate/bigdata/path"
```

When accessed from Python, you'll immediately see the paths have all changed:

```python
>>> for name, location in paths.items():
>>>     print(f"{name}: {location}")
data_path: /alternate/bigdata/path/ReproAllTheThings/data
raw_data_path: /alternate/bigdata/path/ReproAllTheThings/data/raw
interim_data_path: /alternate/bigdata/path/ReproAllTheThings/data/interim
processed_data_path: /alternate/bigdata/path/ReproAllTheThings/data/processed
project_path: /alternate/bigdata/path/ReproAllTheThings
```
as has `config.ini`:

```bash
>>> cat catalog/config.ini
[Paths]
data_path = ${project_path}/data
raw_data_path = ${data_path}/raw
interim_data_path = ${data_path}/interim
processed_data_path = ${data_path}/processed
project_path:/alternate/bigdata/path
```

### Accessing the unresolved paths from Python

If you ever need to see the raw (non-resolved) versions of the paths from within Python, use `paths.data`:

```python
>>> for name, location in paths.data.items():
>>>     print(f"{name}: {location}")
data_path:${project_path}/data
raw_data_path:${data_path}/raw
interim_data_path:${data_path}/interim
processed_data_path:${data_path}/processed
project_path:/alternate/bigdata/path
```

### For more information
```python
>>> from  {{ cookiecutter.module_name }} import paths
>>> help(paths)
```
