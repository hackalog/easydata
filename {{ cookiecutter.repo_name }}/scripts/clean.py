import glob
import os
import os.path
import shutil


for path, dirs, files in os.walk("."):
    try:
        i_pycache = dirs.index("__pycache__")
        shutil.rmtree(os.path.join(path, "__pycache__"))
        del dirs[i_pycache]
    except ValueError:
        pass

    for file_ in files:
        file = os.path.join(path, file_)
        ext = os.path.splitext(file)[1]
        if any(ext.endswith(x) for x in ["pyo", "pyc"]):
            os.unlink(file)

for p in glob.glob(".make.*"):
    os.unlink(p)
