from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
PROJECT = PACKAGE.parents[1]
DATA = PACKAGE / 'data'
ASSETS = PACKAGE / 'assets'
REFERENCES = PACKAGE / 'references'
OUTPUT = PACKAGE / 'output'
OUTPUT.mkdir(parents=True, exist_ok=True)
