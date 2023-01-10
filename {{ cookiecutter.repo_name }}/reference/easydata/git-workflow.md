# The EasyData Git Workflow
Here's our suggestion for a reliable git workflow that works well in **small team settings**; e.g. when using [Easydata][easydata] in a group setting.

## Git configuration

If you haven't yet done so, please follow the instrucitons
in our [Git Configuration Guide](git-configuration.md) first.

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

### Am I working from the latest `{{cookiecutter.default_branch}}`?
Now that your `{{cookiecutter.default_branch}}` branch is up-to-date with both `origin` and `upstream`, you should use it to update your local working branches. If you are already developing in a branch called, e.g. `my_branch`, do this before writing any more code:

```bash
git checkout my_branch
git merge {{cookiecutter.default_branch}}
git push origin my_branch
```

### Clean up the junk
With your local `{{cookiecutter.default_branch}}`, `origin/{{cookiecutter.default_branch}}` and `upstream/{{cookiecutter.default_branch}}` all in sync, we like to clean up any old branches that are fully merged (and hence, can be deleted without data loss.)
```bash
git branch --merged {{cookiecutter.default_branch}}
git branch -d <name_of_merged_branch>
```
A really great feature of `git branch -d` is that it will refuse to remove a branch that hasn't been fully merged into another. Thus it's safe to use without any fear of data loss.


### Start the day
Once you've finished all your merge tasks, you can create a clean working branch from the latest `{{cookiecutter.default_branch}}` by doing a:
```bash
git checkout {{cookiecutter.default_branch}}
git checkout -b new_branch_name
```

That's it! Do you have any suggestions for improvements to this workflow? Drop us a line or file an issue in our
[easydata issue tracker].

[easydata issue tracker]: https://github.com/hackalog/easydata/issues
[easydata]: https://github.com/hackalog/easydata