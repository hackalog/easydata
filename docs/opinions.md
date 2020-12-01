# Easydata Opinions

There are some opinions implicit in the project structure that have grown out of our experience with what works and what doesn't when collaborating on data science projects. Some of the opinions are about workflows, and some of the opinions are about tools that make life easier. Here are some of the beliefs which this project is built on—if you've got thoughts, please [contribute or share them](#contributing).

### Data is immutable

Don't ever edit your raw data, especially not manually. Don't overwrite your raw data. Don't save multiple versions of the raw data. Treat the data (and its format) as immutable. The code you write should move the raw data through a pipeline to your final analysis. You shouldn't have to run all of the steps every time you want to make a new figure (see [Analysis is a DAG](#analysis-is-a-dag)), but anyone should be able to reproduce the final products with only the code in {{ cookiecutter.module_name }} and the data in `data/raw`.

Also, if data is immutable, it doesn't need source control in the same way that code does. Therefore, ***by default, the data folder is included in the `.gitignore` file.*** If you have a small amount of data that rarely changes, you may want to include the data in the repository. Github currently warns if files are over 50MB and rejects files over 100MB. Some other options for storing/syncing large data include [AWS S3](https://aws.amazon.com/s3/) with a syncing tool (e.g., [`s3cmd`](http://s3tools.org/s3cmd)), [Git Large File Storage](https://git-lfs.github.com/), [Git Annex](https://git-annex.branchable.com/), and [dat](http://dat-data.com/).

### Shared workflows matter
Shared workflows matter in enabling reproducible results and smoother collaboration. That's why we include a suite of recommendeded (but lightweight) workflows that help you to collaborate with others in our `framework-docs`. Use them out-of-the-box for a workshop, or adapt them to suit your team's needs. Either way, we recommend that shared workflows stay with the project and include a few key elements:

* Contributor guidelines
* A shared git workflow
* How to submit issues, questions, or get help
* Where to put different types of project materials such as code, notebooks for story-telling, documentation, visualizations, other deliverables
* Which licenses to use (aka. terms for sharing)

### Notebooks are for exploration and communication

Notebook packages like the [Jupyter notebook](http://jupyter.org/), [Beaker notebook](http://beakernotebook.com/), [Zeppelin](http://zeppelin-project.org/), and other literate programming tools are very effective for exploratory data analysis. However, these tools can be less effective for reproducing an analysis. When we use notebooks in our work, we often subdivide the `notebooks` folder. For example, `notebooks/exploratory` contains initial explorations, whereas `notebooks/reports` is more polished work that can be exported as html to the `reports` directory.

Since notebooks are challenging objects for source control (e.g., diffs of the `json` are often not human-readable and merging is near impossible), we recommended not collaborating directly with others on Jupyter notebooks. There are two steps we recommend for using notebooks effectively:

 1. Follow a naming convention that shows the owner and the order the analysis was done in. We use the format `<step>-<ghuser>-<description>.ipynb` (e.g., `0.3-bull-visualize-distributions.ipynb`).

 2. Refactor the good parts. Don't write code to do the same task in multiple notebooks. If it's a data preprocessing task, put it in the pipeline at `src/data/make_dataset.py` and load data from `data/interim`. If it's useful utility code, refactor it to `src`.

 Now by default we turn the project into a Python package (see the `setup.py` file). You can import your code and use it in notebooks with a cell like the following:

```
# OPTIONAL: Load the "autoreload" extension so that code can change
%load_ext autoreload

# OPTIONAL: always reload modules so that as you change code in src, it gets loaded
%autoreload 2

from src.data import make_dataset
```

### Analysis is a DAG

Often in an analysis you have long-running steps that preprocess data or train models. If these steps have been run already (and you have stored the output somewhere like the `data/interim` directory), you don't want to wait to rerun them every time. We prefer [`make`](https://www.gnu.org/software/make/) for managing steps that depend on each other, especially the long-running ones. Make is a common tool on Unix-based platforms (and [is available for Windows]()). Following the [`make` documentation](https://www.gnu.org/software/make/), [Makefile conventions](https://www.gnu.org/prep/standards/html_node/Makefile-Conventions.html#Makefile-Conventions), and [portability guide](http://www.gnu.org/savannah-checkouts/gnu/autoconf/manual/autoconf-2.69/html_node/Portable-Make.html#Portable-Make) will help ensure your Makefiles work effectively across systems. Here are [some](http://zmjones.com/make/) [examples](http://blog.kaggle.com/2012/10/15/make-for-data-scientists/) to [get started](https://web.archive.org/web/20150206054212/http://www.bioinformaticszen.com/post/decomplected-workflows-makefiles/). A number of data folks use `make` as their tool of choice, including [Mike Bostock](https://bost.ocks.org/mike/make/).

There are other tools for managing DAGs that are written in Python instead of a DSL (e.g., [Paver](http://paver.github.io/paver/#), [Luigi](http://luigi.readthedocs.org/en/stable/index.html), [Airflow](http://pythonhosted.org/airflow/cli.html), [Snakemake](https://bitbucket.org/snakemake/snakemake/wiki/Home), [Ruffus](http://www.ruffus.org.uk/), or [Joblib](https://pythonhosted.org/joblib/memory.html)). Feel free to use these if they are more appropriate for your analysis.

### Build from the environment up

The first step in reproducing an analysis is always reproducing the computational environment it was run in. You need the same tools, the same libraries, and the same versions to make everything play nicely together.

One effective approach to this is use [conda](https://anaconda.org) By listing all of your requirements in the repository (we include a `environment.yml` file) you can easily track the packages needed to recreate the analysis. Here is a good workflow:

 1. Run `make create_environment` when creating a new project
 2. Add new requirements to `environment.yml`, either in the main section (for conda installations), or under the indented `- pip:` line, if it should be pip installed.
 3. Type `make update_environment`

If you have more complex requirements for recreating your environment, consider a virtual machine based approach such as [Docker](https://www.docker.com/) or [Vagrant](https://www.vagrantup.com/). Both of these tools use text-based formats (Dockerfile and Vagrantfile respectively) you can easily add to source control to describe how to create a virtual machine with the requirements you need.

### Keep secrets and configuration out of version control

You _really_ don't want to leak your AWS secret key or Postgres username and password on Github. Enough said — see the [Twelve Factor App](http://12factor.net/config) principles on this point. Here's one way to do this:

#### Store your secrets and config variables in a special file

Create a `.env` file in the project root folder. Thanks to the `.gitignore`, this file should never get committed into the version control repository. Here's an example:

```nohighlight
# example .env file
DATABASE_URL=postgres://username:password@localhost:5432/dbname
AWS_ACCESS_KEY=myaccesskey
AWS_SECRET_ACCESS_KEY=mysecretkey
OTHER_VARIABLE=something
```

#### Use a package to load these variables automatically.

If you look at the stub script in `src/data/make_dataset.py`, it uses a package called [python-dotenv](https://github.com/theskumar/python-dotenv) to load up all the entries in this file as environment variables so they are accessible with `os.environ.get`. Here's an example snippet adapted from the `python-dotenv` documentation:

```python
# src/data/dotenv_example.py
import os
from dotenv import load_dotenv, find_dotenv

# find .env automagically by walking up directories until it's found
dotenv_path = find_dotenv()

# load up the entries as environment variables
load_dotenv(dotenv_path)

database_url = os.environ.get("DATABASE_URL")
other_variable = os.environ.get("OTHER_VARIABLE")
```

### Be conservative in changing the default folder structure

To keep this structure broadly applicable for many different kinds of projects, we think the best approach is to be liberal in changing the folders around for _your_ project, but be conservative in changing the default structure for _all_ projects.