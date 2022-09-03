from subprocess import run

## Tiny script to check if conda, make and git are installed

all_installed = True
for requirement in ['conda', 'make', 'git status']:
    try:
        process_run = run(requirement.split(), capture_output=True)
        if process_run. returncode == 0:
            print(f"{requirement} installed!")
        else:
            print(f"{requirement} does not seem to be installed correctly. See the README for help getting this tool ready.")
            all_installed = False
    except:
        print(f"{requirement} does not seem to be installed correctly. See the README for help getting this tool ready.")
        all_installed = False

if all_installed:
    print("You're ready! Type 'make' for more options")
