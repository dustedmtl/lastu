"""Write Windows/macos version number to file."""

import os
import sys
import re

# Get the value of the VER environment variable
ver = os.environ.get('VER')
if ver is None:
    print("No version number recorded to environment variable VER; exiting")
    sys.exit()

if sys.platform.startswith('win32'):
    # Read the contents of the file
    with open('win-version-tpl.yaml', 'r') as file:
        contents = file.read()

    # Replace all occurrences of 'VERSION' with the value of the VER environment variable
    contents = re.sub('VERSION', ver, contents)

    # Write the modified contents back to the file
    with open('win-version.yaml', 'w') as file:
        file.write(contents)
elif sys.platform.startswith('darwin'):
    newcontents = []
    # Read the contents of the file
    with open('ui-qt6.spec', 'r') as file:
        for line in file.readlines():
            newcontents.append(line.strip('\n'))

            # Add a new line for version
            if 'bundle_identifier' in line:
                newcontents.append(f'    version="{ver}"')

    newcontents.append('\n')
    # Write the modified contents back to the file
    with open('ui-qt6.new.spec', 'w') as file:
        file.write('\n'.join(newcontents))
