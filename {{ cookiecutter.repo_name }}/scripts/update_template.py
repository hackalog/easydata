#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016, Abdó Roig-Maranges <abdo.roig@gmail.com>
# All rights reserved.

# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
#    may be used to endorse or promote products derived from this software without
#    specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import os
import sys
import json
import shutil
import subprocess
import json
from cookiecutter.main import cookiecutter


class TemporaryWorkdir():
    """Context Manager for a temporary working directory of a branch in a git repo"""

    def __init__(self, path, repo, branch='master'):
        self.repo = repo
        self.path = path
        self.branch = branch

    def __enter__(self):
        if not os.path.exists(os.path.join(self.repo, ".git")):
            raise Exception("Not a git repository: %s" % self.repo)

        if os.path.exists(self.path):
            raise Exception("Temporary directory already exists: %s" % self.path)

        os.makedirs(self.path)
        subprocess.run(["git", "worktree",  "add", "--no-checkout", self.path, self.branch],
                       cwd=self.repo)

    def __exit__(self, type, value, traceback):
        shutil.rmtree(self.path)
        subprocess.run(["git", "worktree", "prune"], cwd=self.repo)


def update_template(template_url, root, branch):
    """Update template branch from a template url"""
    tmpdir       = os.path.join(root, ".git", "cookiecutter")
    project_slug = os.path.basename(root)
    config_file  = os.path.join(root, ".cookiecutter.json")
    tmp_workdir  = os.path.join(tmpdir, project_slug)

    # read context from file.
    context = None
    if os.path.exists(config_file):
        with open(config_file, 'r') as fd:
            context = json.loads(fd.read())
            context['project_slug'] = project_slug

    # create a template branch if necessary
    if subprocess.run(["git", "rev-parse", "-q", "--verify", branch], cwd=root).returncode != 0:
        firstref = subprocess.run(["git", "rev-list", "--max-parents=0", "HEAD"],
                                  cwd=root,
                                  stdout=subprocess.PIPE,
                                  universal_newlines=True).stdout.strip()
        subprocess.run(["git", "branch", branch, firstref])

    with TemporaryWorkdir(tmp_workdir, repo=root, branch=branch):
        # update the template
        cookiecutter(template_url,
                     no_input=(context != None),
                     extra_context=context,
                     overwrite_if_exists=True,
                     output_dir=tmpdir)

        # commit to template branch
        subprocess.run(["git", "add", "-A", "."], cwd=tmp_workdir)
        subprocess.run(["git", "commit", "-m", "Update template"],
                       cwd=tmp_workdir)


if __name__ == '__main__':
    with open(sys.argv[1], 'r') as fd:
        context = json.load(fd)

    update_template(context['_template'], os.getcwd(), branch=sys.argv[2])
