# Packaging an executable

## Setup
- Clone the repository
  - `git clone`
- Create a virtual environment for packaging (packenv)
  - `python3 -m venv packenv`
  - See also: https://docs.python.org/3/library/venv.html
- Activate virtual environment
  - Mac:
    - `source packenv/bin/activate`
  - Windows:
    - `packenv\Scripts\activate.bat`
 - Install requirements to packenv
   - `pip3 install -r packaging-requirements.txt`

## Building
- Activate virtual environment (see above)
- Build
  - Mac:
    - export VER=0.0.X.0
    - `python write-version.py`
      - generates file `ui-qt6.new.spec` based on `ui-qt6.spec`
    - Preferred: `pyinstaller ui-qt6.new.spec`
      - OR `pyinstaller --windowed ui-qt6.py`
  - Windows:
    - Update version number and version file 
      - `set VER=0.0.X.0`
      - `python write-version.py`
        - generates file `win-version.yaml` based on `win-version-tpl.yaml`
     - `create-version-file win-version.yaml --outfile win-version.txt`
        - generates version file that is usable in Windows
    - Preferred: `pyinstaller ui-qt6-win.spec`
      - OR `pyinstaller --onefile ui-qt6.py`
  - See also : https://pyinstaller.org/en/stable/usage.html

