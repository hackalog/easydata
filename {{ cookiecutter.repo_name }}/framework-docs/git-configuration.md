# Setting up git and Checking Out the Repo

**Note**: These instructions assume you are using SSH keys (and not HTTPS authentication) with {{ cookiecutter.upstream_location }}. If you haven't set up SSH access to your repo host, see [Configuring SSH Access to Github or Gitlab][git-ssh]. This also includes instructions for using more than one account with SSH keys.

[git-ssh]: https://github.com/hackalog/cookiecutter-easydata/wiki/Configuring-SSH-Access-to-Github-or-GitLab

## Git Configuration
When sharing a git repo with a small team, your code usually lives in at least 3 different places:

* "local" refers to any git checkout on a local machine (or JupyterHub instance). This is where you work most of the time.
* `upstream` refers to the shared Easydata repo on {{ cookiecutter.upstream_location}}; i.e. the **team repo**,
* `origin` refers to your **personal fork** of the shared Easydata repo. It also lives on {{ cookiecutter.upstream_location}}.

### Create a Personal Fork

We strongly recommend you make all your edits on a personal fork of this repo. Here's how to create such a fork:

* On Github or Gitlab, press the Fork button in the top right corner.
* On Bitbucket, press the "+" icon on the left and choose **Fork this Repo**

### Local, `origin`, and `upstream`
git calls `upstream` (the **team repo**), and `origin` (your **personal fork** of the team repo) "remote" branches. Here's how to create them.

Create a local git checkout by cloning your personal fork:
```bash
git clone git@{{ cookiecutter.upstream_location }}:<your_git_handle>/{{cookiecutter.repo_name}}.git
```
Add the team (shared) repo as a remote branch named `upstream`:
```bash
  cd {{cookiecutter.repo_name}}
  git remote add upstream git@{{ cookiecutter.upstream_location }}:<upstream-repo>/{{cookiecutter.repo_name}}.git
```

You can verify that these branches are configured correctly by typing

```
>>> git remote -v
origin	git@{{ cookiecutter.upstream_location }}:<your_git_handle>/{{cookiecutter.repo_name}}.git (fetch)
origin	git@{{ cookiecutter.upstream_location }}:<your_git_handle>/{{cookiecutter.repo_name}}.git (push)
upstream	git@{{ cookiecutter.upstream_location }}:<upstream-repo>/{{cookiecutter.repo_name}}.git (fetch)
upstream	git@{{ cookiecutter.upstream_location }}:<upstream-repo>/{{cookiecutter.repo_name}}.git (push)
```
or if you use HTTPS-based authentication:
```
origin	https://{{ cookiecutter.upstream_location }}/<your_git_handle>/{{cookiecutter.repo_name}}.git (fetch)
origin	https://{{ cookiecutter.upstream_location }}/<your_git_handle>/{{cookiecutter.repo_name}}.git (push)
upstream	https://{{ cookiecutter.upstream_location }}/<upstream-repo>/{{cookiecutter.repo_name}}.git (fetch)
upstream	https://{{ cookiecutter.upstream_location }}/<upstream-repo>/{{cookiecutter.repo_name}}.git (push)
```

### Do Your Work in Branches
To make life easiest, we recommend you do all your development **in branches**, and use your {{cookiecutter.default_branch}} branch **only** for tracking changes in the shared `upstream/{{cookiecutter.default_branch}}`. This combination makes it much easier not only to stay up to date with changes in the shared project repo, but also makes it easier to submit Pull/Merge Requests (PRs) against the upstream project repository should you want to share your code or data.

### A Useful Git Workflow
Once you've got your local, `origin`, and `upstream` branches configured, you can follow the instructions in this handy [Git Workflow Cheat Sheet](git-workflow.md) to keep your working copy of the repo in sync with the others.
