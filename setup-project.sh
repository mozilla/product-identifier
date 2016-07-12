#!/bin/sh

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

rm -rf onyx-env

virtualenv --python=python2.7 --no-site-packages product-identifier-env
. product-identifier-env/bin/activate


python setup.py develop
pip install -r requirements.txt
