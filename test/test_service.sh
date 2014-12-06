#!/bin/bash

# python service.py 

curl localhost:5000/travis -d 'payload={"number": "134", "repository":{"name": "test", "owner_name": "test_owner"}}'

curl localhost:5000/travis -d 'build=134&repo=test/test2'
