import os
import os.path


here = os.path.basename(os.getcwd())
print("""\
To update easydata on an existing repo, verify that you have an 'easydata' branch

>>> git rev-parse -q --verify easydata

If no output is given, do this:

>>> git rev-list --max-parents=0 HEAD

and copy-paste the output hash in this command:

>>> git branch easydata #PASTE HASH HERE#

Once you have the easydata branch, let's commit ("check in") all your changes,
then merge the new easydata branch into yours:

cd ..
cookiecutter --config-file {here}/.easydata.yml easydata -f --no-input
""")
print("cd " + here)
print("""\
git add -p  # add all the changes
git commit -m "sync with easydata"
git checkout main
git merge easydata
""")
