#!/bin/bash
# Run the tests
PYTHONPATH=$PYTHONPATH:./lib/pymaker py.test --cov=autoline_keeper --cov-report=term --cov-append tests/ $@