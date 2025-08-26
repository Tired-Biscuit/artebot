import sys

import python.tools as tools

if len(sys.argv) > 1:
    tools.add_owner(int(sys.argv[1]))
    print(f"Added {sys.argv[1]} as owner")
    tools.add_admin(int(sys.argv[1]))
    print(f"Added {sys.argv[1]} as owner")