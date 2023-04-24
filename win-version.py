"""Write Windows version number to file."""

import os
import re

# Get the value of the VER environment variable
ver = os.environ.get('VER')

if ver is None:
    print("No version number recorded to environment variable VER; exiting")
    exit()

# Read the contents of the file
with open('win-version-tpl.yaml', 'r') as file:
    contents = file.read()

# Replace all occurrences of 'VERSION' with the value of the VER environment variable
contents = re.sub('VERSION', ver, contents)

# Write the modified contents back to the file
with open('win-version.yaml', 'w') as file:
    file.write(contents)
