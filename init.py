import sys

import python.tools as tools

if len(sys.argv) > 1:
    tools.add_owner(int(sys.argv[1]))
    print(f"Added {sys.argv[1]} as owner")
    with open(tools.datafile_path, "r") as f:
        data = f.read()
        print(data)
    tools.add_admin(int(sys.argv[1]))
    print(f"Added {sys.argv[1]} as admin")
    with open(tools.datafile_path, "r") as f:
        data = f.read()
        print(data)