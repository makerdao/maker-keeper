#!/bin/bash
# Run the tests
PYTHONPATH=$PYTHONPATH:./lib/pymaker py.test --cov=maker_keeper --cov-report=term --cov-append tests/ $@