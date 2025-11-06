#!/bin/sh
#------------------------------------------------------------------------------
# written by: AprendeMX Team
#
# date:       nov-2025
#
# usage:      Build package and upload to PyPi.
#             https://pypi.org/project/edx-oauth2-llavemx/
#
# see: https://www.freecodecamp.org/news/how-to-create-and-upload-your-first-python-package-to-pypi/
#------------------------------------------------------------------------------

python -m pip install --upgrade build

sudo rm -r build
sudo rm -r dist
sudo rm -r edx_oauth2_llavemx.egg-info

python3 -m build --sdist ./
python3 -m build --wheel ./

python3 -m pip install --upgrade twine
twine check dist/*

# PyPi test
twine upload --skip-existing --repository testpypi dist/*

# PyPi
#twine upload --skip-existing dist/*
