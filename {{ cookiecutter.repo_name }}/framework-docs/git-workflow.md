# The Easydata Git Workflow
Here's our suggestion for a reliable git workflow that works well in small team settings using [Easydata][cookiecutter-easydata].

## Git configuration

If you haven't yet done so, please follow the instrucitons
in [Setting up git and Checking Out the Repo](git-configuration.md) first.

## Git Workflow

We suggest you start each day by doing this:

### Where was I? What was I doing? Did I check it in?
Sometimes, you stop work without checking things back in to the repo.
Now, before you do any additional work, is the time to fix that.
```bash
git branch   # what branch am I on?
git status   # are there any files that need checking in?
git add -p   # accept or reject parts of the modified files
git commit -m "put your commit message here"
```

### Did I do any work elsewhere?
Did you make changes to your personal fork, but on a different machine? Make sure your local branch is up-to-date with your personal fork (`origin`):
```bash
git checkout {{cookiecutter.default_branch}}
git fetch origin --prune
git merge origin/{{cookiecutter.default_branch}}
```

### What happened upstream?
Did someone make changes to the `upstream` repo in your absense?
Let's fetch and merge those changes

```bash
git checkout {{cookiecutter.default_branch}}
git fetch upstream --prune
git merge upstream/{{cookiecutter.default_branch}}
git push origin {{cookiecutter.default_branch}}
make update_environment
```

### Update your local branches
Now that your `{{cookiecutter.default_branch}}` branch is up-to-date with both `origin` and `upstream`, you should use it to update your local working branches. If you are already developing in a branch called, e.g. `my_branch`, do this before writing any more code:

```bash
git checkout my_branch
git merge {{cookiecutter.default_branch}}
git push origin my_branch
```

### Start a new branch for the day's work
Create a clean working branch by doing a:
```bash
git checkout {{cookiecutter.default_branch}}
git checkout -b new_branch_name
```

### Clean up the old branches
Now that you're up-to-date, you can clean up any of your old branches that are fully merged (and hence, can be deleted.)
```bash
git branch --merged {{cookiecutter.default_branch}}
git branch -d <name_of_merged_branch>
```

Got any suggestions for improvements to this workflow? File an issue at
[cookiecutter-easydata].

[cookiecutter-easydata]: https://github.com/hackalog/cookiecutter-easydata/