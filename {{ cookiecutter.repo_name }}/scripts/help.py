from argparse import ArgumentParser
import re
import sys


if sys.platform.lower() == "win32":
    def bold(s):
        return s
    def cyan(s):
        return s
else:
    HEY = "\x1e["
    RESET = HEY + "0n"
    def bold(s):
        return HEY + "1n" + s + RESET
    def cyan(s):
        return HEY + "36n" + s + RESET


ap = ArgumentParser()
ap.add_argument("-v", nargs=2, action="append", dest="variables")
ap.add_argument("makefiles", nargs="+")
ns = ap.parse_args(sys.argv[1:])
ls_variables = list(ns.variables)
d_variables = dict(ls_variables)
makefiles = list(ns.makefiles)
if "PROJECT_NAME" not in d_variables:
    print("No project name! Consult with EasyData maintainers.")
    sys.exit(1)
project_name = d_variables["PROJECT_NAME"]

print("*** To get started ***")
print("")
print("  >>> " + bold("make create_environment"))
print("  >>> " + bold("conda activate " + project_name))
print("  >>> " + bold("make update_environment"))

print("")
print(bold("*** Project variables ***"))
print("")

len_name_max = max([len(name) for name, value in ls_variables])
for name, value in ls_variables:
    print(name + " " * (len_name_max - len(name)) + " = " + value)

print("")
print(bold("*** Available rules ***"))
print("")
rules = []
for path in set(makefiles):
    f = open(path, "rb")
    makefile = iter(f.read().split(b"\n"))
    f.close()
    while True:
        try:
            line = next(makefile)
            lines_doc = []
            while line.startswith(b"## "):
                lines_doc.append(line[2:])
                line = next(makefile)
            if len(lines_doc) > 0:
                # We have collected some documentation. Current line now contains the target name.
                target = line.split(b":")[0]
                lines_doc = [
                    re.sub(
                        r"\$\(([-a-zA-Z0-9_]+)\)",
                        lambda m: d_variables.get(m.group(1), b"???"),
                        ll.decode("utf-8")
                    ).strip()
                    for ll in lines_doc
                ]
                rules.append((target.decode("utf-8"), " ".join(lines_doc)))
        except StopIteration:
            break

width_target = max([len(target) for target, _ in rules])
for target, doc in sorted(rules, key=lambda p: p[0]):
    print(cyan(target) + " " * (width_target - len(target)) + "  " + doc)
