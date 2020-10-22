# Sharing your Work

* [Contributor Guidelines and Checklist](#contributor-guide-and-checklist)
* [Best Practices for Sharing](#best-practices-for-sharing)
  * [Sharing Code Using Git and GitLab](#sharing-code-using-git-and-github)
  * [Sharing Datasets](#sharing-datasets)
  * [Sharing Conda Environments](#sharing-conda-environments)
  * [Sharing Notebooks](#sharing-notebooks)
* [Quick Guide to Licenses](#quick-guide-to-licenses)

## Contributor Guidelines and Checklist

The main impetus of following the **recommended workflow** for this project is to help make it easier to share your datasets, code and analyses in a reproducible way and easy-to-use way.

We **want** you to share your work. We understand that your work may still be a **work-in-progress** when you first start to share it. We encourage that. There are three main ways to contribute to this repo:


* **Filing and reporting issues:** Please don't be shy here. Chances are if you encounter an issue, someone else already has, or someone else will encounter the same issue in the future. Reporting helps us to find solutions that will work for everyone. Hacks and your personal work-arounds are not reproducible. No issue is too small. Share the love and let us solve issues as best we can for everyone. Issues include anything from "I had trouble understanding and following the documentation", to feature requests, to bugs in the main code repo.
  1. First up, [make sure that you're working with the most up-to-date version](https://github.com/hackalog/cookiecutter-easydata/wiki/Github-Workflow-Cheat-Sheet) of the codebase.
  1. Check the [troubleshooting guide](conda-environments.md#troubleshooting) to see if a solution has already been documented.
  1. Check if the issue has been reported already. If so, make a comment on the issue to indicate that you're also having said issue.
  1. Finally, if your issue hasn't been resolved at this stage, file an issue. For bugs reports, please include reproducers.
* **Submitting Pull Requests (PRs):** This is the way to share your work if it involves any code. To prepare your PR, follow the [contributor checklist](#contributor-checklist). In the meantime, follow the [recommended best practices](#best-practices-for-sharing) to make your life easier when you are ready to share.

### Contributor Checklist

When is my work ready to share? Let's find out!

When you are ready share your notebook or code with others, you'll be able to tick all of the following boxes.

#### Notebooks and Code
- [ ] Notebooks are in the `notebooks` directory following the [notebook naming convention](notebooks.md#naming-convention).
- [ ] Notebooks load data via the `Dataset.load()` API to access an available Dataset.
- [ ] Functions are in `{{ cookiecutter.module_name }}/user_name` and accessed in notebooks via something like `from {{ cookiecutter.module_name }}.user_name import my_function`. If you have  `def my_function` in your notebook or anything more elaborate, there's a good chance that it should be in the `{{ cookiecutter.module_name }}` module.
- [ ] Notebook cells run sequentially (i.e. **Kernel->Restart & Run All** runs to completion successfully).
- [ ] *(Optional but generally recommended)*: All notebook cell output has been cleared before checking it in (i.e. **Kernel->Restart & Clear Output** before saving).

#### Licences
- [ ] Decide on a [license for your data derived work (e.g. images)](#quick-guide-to-licenses) and if it's not the same as that of the dataset you used, mark it appropriately as per your license of choice (assuming it's compatible with the dataset's license). By default, the license of derived work will be the same as the dataset it came from.

#### Environment and Tests
- [ ] Share your conda environment. Check in your `environment.yml` file if you've made any changes.
  * If there's any chance that you added something to the conda environment needed to run your code that was **not** added via your `environment.yml` file as per [Setting up and Maintaining your Conda Environment (Reproducibly)](conda-environments.md), [delete your environment and recreate it](conda-environments.md#nuke-it-from-orbit).
- [ ] *(Optional)* Make sure all tests pass (run `make test`). This will test all of the dataset integration so if you don't have a lot of room on your machine (as it will build all the the datasets if you haven't yet), you may want to skip this step.
- [ ] At least, make sure all of the tests for your code pass. To subselect your tests you can run `pytest --pyargs {{ cookiecutter.module_name }} -k your_test_filename`.

#### Final Checks
- [ ] You've [merged the latest version](https://github.com/hackalog/cookiecutter-easydata/wiki/Github-Workflow-Cheat-Sheet) of `upstream/master` into your branch.
- [ ] [Submitted a PR via GitLab](#how-to-submit-a-PR) in **Draft** status and checked the PR diff to make sure that you aren't missing anything critical, you're not adding anything extraneous, and you don't have any merge conflicts.

Once this checklist is complete, take your **PR** out of **Draft** status. It's ready to go!

As a person who is trying to contribute and share your work with others, it may at times feel like this is a lot of work. We get that, and find it useful to think of it this way: for every 5 minutes extra that you put into making your work reproducible, everyone else who tries to run or use your work will spend at least 5 minutes less trying to get it to work for them. In other words, making your work reproducible is part of being a good citizen and helping us all to learn from each other as we go. Thank you for helping us to share and use your work!


## Best Practices for Sharing
### Sharing Code Using Git and GitLab

Quick References:

* Keeping up-to-date: [Our GitLab Workflow](https://github.com/hackalog/cookiecutter-easydata/wiki/Github-Workflow-Cheat-Sheet)
* Recommended [Git tutorial](https://github.com/hackalog/cookiecutter-easydata/wiki/Git-Tutorial)


There are several ways to use Git and GitLab successfully, and a lot more ways to use them unsuccessfully when working with lots of other people. Here are some best practices that we suggest you use to make your life, and our lives easier. This workflow we suggest makes choosing which changes to put in a pull request easier, and helps to avoid crazy merge conflicts.

First off, follow the [Getting Started](../README.md#getting-started) instructions for setting yourself up to work off of your own fork. The idea here will be to keep `upstream/master`, your local `master` and your `origin/master` all in sync with each other.

Any changes should be made in a separate branch---**not** your `master`---that you push up to your fork. Eventually, when you're ready to submit a PR, you'll do so from the branch that you've been working on. When you push to your `origin/branch_name`, you should get prompted in the terminal by `git` with a URL you can follow to submit a PR. To do so:

1. Make sure your `master` is up-to-date with upstream `git fetch upstream` and `git merge upstream/master`
1. Make sure your environment is up-to-date with upstream `make update_environment`
1. Start your work (from your up-to-date `master`) in a new branch: `git checkout -b my_new_branch`
1. Commit all your changes to `my_new_branch` (as per the [GitLab Workflow](https://github.com/hackalog/cookiecutter-easydata/wiki/Github-Workflow-Cheat-Sheet))


You can pretty much blindly do this by following the [GitLab Workflow](https://github.com/hackalog/cookiecutter-easydata/wiki/Github-Workflow-Cheat-Sheet) religiously.

#### How to submit a PR

1. Push to your GitLab fork by `git push origin my_new_branch`.
1. If this is the first time you do this from `my_new_branch`, you'll be prompted with a URL from your terminal for how to create a PR. Otherwise, if you go to GitLab, you'll see a yellow banner at the top of the screen prompting you to submit a PR (as long as you're not out of sync with the `upstream master`, in which case, re-sync your branch).
1. You have the option to submit a PR in **Draft** status. Select this if you have a work in progress. It disables the ability to merge your PR.
1. Once you submit your PR, there may be a yellow dot or red X beside your PR. This is because we have tests set up in CircleCI. If you are working in a private repo, you need to authorize access to CircleCI on your fork for tests to run successfully. To do so, follow the link to CircleCI and **authorize gitlab** on your fork of the repo.
1. When ready, take your PR out of **Draft** status.


#### General Git Suggestions:
* Never commit your changes to your `master` branch. Always work off of a branch. Then you always have a clean local copy of `upstream/master` to work off of.
* Stick to **basic git commands** unless you *really* know what you're doing. (e.g. use `add`, `fetch`, `merge`, `commit`, `diff`, `rm`, `mv`)
* While sometimes convenient, avoid using `git pull` from remotes. Or just general avoid using `git pull`. Use `git fetch` then `git merge` instead.
* Use `git add -p` instead of `git add` to break up your commits into logical pieces rather than one big snotball of changes.

### Sharing Datasets

Most of the infrastructure behind the scenes in this repo is set up for sharing datasets reliably and reproducibly without ever checking it in. We use **recipes** for making Datasets instead. So in short, don't check in data. And use the `Dataset.load()` API.

In order to convert your data to a `Dataset` object, we will need to generate a catalog recipe, that uses a custom function for processing your raw data. Doing so allows us to document all the munging, pre-processing, and data verification necessary to reproducibly build the dataset. Details on how to do this can be found on the [cookiecutter-easydata repo](https://github.com/hackalog/cookiecutter-easydata), but it's likely better to ask the maintainers of this project can point you in the right direction for how to get a Dataset added to this project.

For more on `Dataset` objects, see [Getting and Using Datasets](datasets.md).

For more on licenses, see [below](#quick-guide-to-licenses).

### Sharing conda environments
In order to make sharing virtual environments easy, the repo includes `make` commands that you can use to manage your environment via an `environment.yml` file (and corresponding `environment.${ARCH}.lock.yml` file). By [setting up and maintaining your conda environment reproducibly](conda-environments.md), sharing your environment is as easy as including any changes to your `environment.yml` file in your PR.

If there's any chance that you added something to the conda environment needed to run your code that was **not** added via your `environment.yml`, [delete your environment, recreate it](conda-environments.md#nuke-it-from-orbit) and then make the appropriate changes to your `environment.yml` file.

Remember to `make update_environment` regularly after fetching and merging the `upstream` remote to keep your conda environment up-to-date with the main repo.

### Sharing notebooks and code
We're keen on sharing notebooks for sharing stories and analyses. Best practices can be found in [using notebooks for sharing your analysis](notebooks.md). A short list of reminders:

* Follow the [notebook naming convention](notebooks.md#naming-convention)
* Use the [`Dataset.load()` API](datasets.md) for accessing data
* Put [code in the `{{ cookiecutter.module_name }}` module](notebooks.md#on-code) under `{{ cookiecutter.module_name }}/xyz` where `xyz` is your (the author's) initials (as in the notebook naming convention)
* Run **Kernel->Restart & Run All** and optionally **Kernel->Restart & Clear Output** before saving and checking in your notebooks

## Quick Guide to Licenses
Work in progress...Add some references

### Quick References

* [README](../README.md)
* [Setting up and Maintaining your Conda Environment Reproducibly](conda-environments.md)
* [Getting and Using Datasets](datasets.md)
* [Using Notebooks for Analysis](notebooks.md)
* [Sharing your Work](sharing-your-work.md)
* [Troubleshooting Guide](troubleshooting.md)
