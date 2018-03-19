#!/bin/bash -ex

cd "$(dirname "$0")"

# From: 'pip install flake8'
python2 -m flake8 $(find * -name '*.py')

# Test with Python2.7+ and Python3.x
export PYTHONPATH=$(dirname "$0"):${PYTHONPATH}
python2 -m pytest -vvv --cov-report=term-missing --cov=datahammer
python3 -m pytest -vvv --cov-report=term-missing --cov=datahammer

# Validate the README.rst file.  On Fedora "rst2html" is part of "python-docutils".
for base in README EXAMPLES; do
    rst2html --cloak-email-addresses --compact-lists --no-raw --smart-quotes=no \
	 ${base}.rst > /tmp/${base}.html
done
