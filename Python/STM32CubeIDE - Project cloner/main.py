import argparse
import re
from distutils.dir_util import copy_tree
from os import remove, walk
from os.path import basename, dirname, exists, isfile, join, realpath
from pathlib import Path
from shutil import copyfile

from colorama import Fore
from consolemenu import ConsoleMenu
from consolemenu.items import FunctionItem

def get_projects(root: str) -> list:

    if not exists(root):
        return []
    
    valid_projects = []

    #? Check if a folder has all the necessary files
    for path, subdirs, files in walk(root):

        cproject = False
        project = False

        for name in files:
            if name == ".cproject":
                cproject = True
            elif name == ".project":
                project = True
            
            if all([cproject, project]):
                break
        
        if all([cproject, project]):
            valid_projects.append(dirname(path))
    
    return valid_projects

def clone_project(src: str) -> None:

    stm32cubeide = "STM32CubeIDE"
    cproject = ".cproject"
    project = ".project"

    print(f"{Fore.WHITE}Selected project: {Fore.YELLOW}{src}{Fore.WHITE}")

    new_project_name = str(input(f"{Fore.WHITE}Project name: {Fore.YELLOW}"))
    new_project_name = new_project_name.replace(" ","_")
    new_project = join(root, new_project_name)

    if exists(new_project):
        input(f'{Fore.WHITE}[{Fore.LIGHTRED_EX}ERROR{Fore.WHITE}] "{basename(new_project)}" already exists{Fore.WHITE}')
        return

    old_project_name = src
    old_project = join(root, old_project_name)

    #? Copy project and replace files names
    print(f'{Fore.LIGHTBLACK_EX}[*] Cloning project...{Fore.WHITE}',end="")
    copy_tree(old_project, new_project)
    print(f'{Fore.LIGHTBLACK_EX}{Fore.WHITE}',end="\r")

    print(f'{Fore.LIGHTBLACK_EX}[*] Replacing files names...{Fore.WHITE}',end="")
    for path, subdirs, files in walk(new_project):
        for name in files:
            if old_project_name in name:
                copyfile(join(path, name), join(path, name.replace(old_project_name, new_project_name)))
                remove(join(path, name))
    print(f'{Fore.LIGHTBLACK_EX}{Fore.WHITE}',end="\r")

    #? Modify <name>...</name> in .project and locationURIs
    print(f'{Fore.LIGHTBLACK_EX}[*] Modifying .project...{Fore.WHITE}',end="")
    with open(join(old_project, stm32cubeide, project), "r", encoding="utf-8") as f:
        content = f.read()

    start = content.index("<name>") + 6
    stop = content.index("</name>")

    content = f"{content[:start]}{new_project_name} - project{content[stop:]}"
    content = content.replace(old_project_name, new_project_name)

    with open(join(new_project, stm32cubeide, project), "w+", encoding="utf-8") as f:
        f.write(content)

    if isfile(join(new_project, project)):
        remove(join(new_project, project))
    print(f'{Fore.LIGHTBLACK_EX}{Fore.WHITE}',end="\r")

    #? Modify .cproject
    print(f'{Fore.LIGHTBLACK_EX}[*] Modifying .cproject...{Fore.WHITE}',end="")
    with open(join(old_project, stm32cubeide, cproject), "r", encoding="utf-8") as f:
        content = f.read()

    occurrencies = [o.start() for o in re.finditer(old_project_name, content)]
    listOptionValues = [content[content.rindex("<", 0, occurrence):content.index('"', occurrence)] for occurrence in occurrencies]

    parsed_values = []

    for listOptionValue in listOptionValues:
        new_value = listOptionValue.replace(old_project_name, new_project_name)
        content = content.replace(listOptionValue, new_value)
        
        if new_value in parsed_values:
            continue

        parsed_values.append(new_value)

        if 'value="' in listOptionValue and 'bsp/' in listOptionValue:
            tmp = listOptionValue[listOptionValue.index('value="') + 7:]

            path = Path(join(old_project, stm32cubeide, cproject))
            path = str((path / tmp).resolve())
            copy_tree(path, join(dirname(path), new_project_name))

            for path, subdirs, files in walk(join(dirname(path), new_project_name)):
                for name in files:
                    if old_project_name in name:
                        with open(join(path, name), "rb", ) as f:
                            data = f.read()

                        if name.endswith(".c") or name.endswith(".h"):
                            data = data.decode().replace(old_project_name, new_project_name).encode()

                        with open(join(path, name.replace(old_project_name, new_project_name)), "wb+", ) as f:
                            f.write(data)

                        remove(join(path, name))

    with open(join(new_project, stm32cubeide, cproject), "w+", encoding="utf-8") as f:
        f.write(content)
    print(f'{Fore.LIGHTBLACK_EX}{Fore.WHITE}',end="\r")

    print(f'{Fore.LIGHTBLACK_EX}[*] Finishing...{Fore.WHITE}',end="")
    for path, subdirs, files in walk(new_project):
        for name in files:

            if not name.endswith(".c") and not name.endswith(".h"):
                continue

            full_path = join(path, name)
            
            with open(full_path, "r", encoding="ISO-8859-1") as f:
                content = f.read()
            
            if content.find(old_project_name) != -1:
                content = content.replace(old_project_name, new_project_name)

                with open(full_path, "w+", encoding="ISO-8859-1") as f:
                    f.write(content)
    print(f'{Fore.LIGHTBLACK_EX}{Fore.WHITE}',end="\r")

    input(f'{Fore.WHITE}[{Fore.LIGHTGREEN_EX}INFO{Fore.WHITE}] "{basename(new_project)}" successfully created{Fore.WHITE}')

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=str, required=False, help="Projects folder. If not specified, the root folder will be the current directory")
    args = parser.parse_args()
    root = args.root if args.root != None else dirname(realpath(__file__))
    root = "C:\\Users\\sassi\\Documents\\Universita\\Terzo anno\\Tesi e Tirocinio\\spark_sdk_v1.1.0\\app\\example"

    menu = ConsoleMenu("STM32CubeIDE - Project cloner", prologue_text="List of cloneable projects:")

    for project in get_projects(root=root):
        item = FunctionItem(basename(project), clone_project, [basename(project)], should_exit=True)
        menu.append_item(item)

    menu.show()
