#!/bin/bash

echo "Building Python Sandbox..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
virtualenv -p `which python3` $SCRIPT_DIR/venv
source $SCRIPT_DIR/venv/bin/activate
pip install -e $SCRIPT_DIR/.

# cd $SCRIPT_DIR
# echo "Initializing DB..."
# python -c "from app import db; db.create_all()"
