# Building an executable

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
    - `pyinstaller --windowed ui-qt6.py`
  - Windows:
    - `pyinstaller --onefile ui-qt6.py`
  - See also : https://pyinstaller.org/en/stable/usage.html

