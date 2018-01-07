#!/bin/bash

# Change into the directory the script lives in.
cd $(readlink -f $(dirname ${0}))

/usr/bin/env python3.6 -m neko
exit ${?}
