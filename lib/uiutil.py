"""Utilities for user interface."""

# pylint: disable=invalid-name, line-too-long

# from typing import List, Dict, Tuple, Optional, Callable, Iterable
from typing import Optional, Tuple
import sys
import os
import logging
import configparser
from pathlib import Path

logger = logging.getLogger('wm2')
# logger.setLevel(logging.DEBUG)


class ConfigurationError(Exception):
    """Configuration error class."""

    def __init__(self, text, *args):
        """Initialize error class."""
        super().__init__(args)
        self.text = text

    def __str__(self):
        """Return error text."""
        return f'Issue with configuration: {self.text}'


def get_macos_path(currentdir: str):
    """Get correct working directory for MacOS."""
    while True:
        parent, lastdir = os.path.split(currentdir)
        # logger.debug('Parent: %s, lastdir: %s', parent, lastdir)
        if lastdir in ['Contents', 'MacOS'] or lastdir.endswith('.app'):
            currentdir = parent
        else:
            break
    return currentdir


def get_windows_path(currentdir: str):
    """Get correct working directory for Windows."""
    # FIXME: actually implement this
    while True:
        parent, lastdir = os.path.split(currentdir)
        logger.debug('Parent: %s, lastdir: %s', parent, lastdir)
        if lastdir in ['Contents', 'MacOS'] or lastdir.endswith('.app'):
            currentdir = parent
        else:
            break
    return currentdir


def get_config(filename: str) -> Tuple[Optional[configparser.ConfigParser], Optional[str]]:
    """
    Get program configuration and current working directory.

    Look for ini file in three places:
    - current directory
    - guessed parent-ish directory (if this is an frozen exe)
    - home directory
    """
    config = configparser.ConfigParser()

    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        logger.debug('Running in a PyInstaller bundle')
    else:
        logger.debug('Running in a normal Python process')

    currfn = os.path.join('.', filename)
    if os.path.exists(currfn):
        logger.debug('Using %s as configuration file', currfn)
        config.read(currfn)
        return config, '.'

    basedir = None

    appcwd = os.path.dirname(sys.argv[0])
    logger.debug('Application current working directory: %s', appcwd)

    # Check parent directories
    if len(appcwd) > 0:
        if sys.platform.startswith('darwin'):
            basedir = get_macos_path(appcwd)
        elif sys.platform.startswith('win32'):
            basedir = get_windows_path(appcwd)
        else:
            # unsupported
            ...
        logger.debug("Got base dir from system: %s", basedir)

    if basedir:
        currfn = os.path.join(basedir, filename)
        if os.path.exists(currfn):
            logger.debug('Using %s as configuration file', currfn)
            config.read(currfn)
            return config, basedir

    homedir = str(Path.home())
    currfn = os.path.join(homedir, filename)
    if os.path.exists(currfn):
        logger.debug('Using %s as configuration file', currfn)
        config.read(currfn)
        return config, basedir

    return None, basedir


def get_configvar(cfg: configparser.ConfigParser,
                  section: str, key: str) -> Optional[str]:
    """Get configuration variable."""
    if not cfg:
        return None
    homedir = str(Path.home())
    try:
        value = cfg.get(section, key)
        value = value.replace('~', str(homedir))
        return value
    except Exception as e:
        logger.warning('Issue with config: section %s key %s: %s', section, key, e)
    return None
