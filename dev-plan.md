
# Dev Plan
This file details the steps we need to take to get the project to a production-ready state.




## Tests
[] add tests (with Pytest)
[] run tests and make sure they pass

## Documentation
[] add a quickstart guide in README.md
[] add a flow diagram of the MCP flow with the Permit.io authorization
[] Add explanation on identity mode and how to configure it, including JWT configuration
[] improve the example server and better explain its flow
[] add more details on how to get started in README.md
[] document all the settings in the config file (in the config.py file and in the README.md)
[] improve inline documentation and docstrings


## Setup publishing and CI/CD
[] create a make file to run the tests, linting, formatting, type checking, and security scanning, and publishing to pypi
[] add a git flow and a github action to run the make file
[] add a github action to run tests
[] add a github action to run linting
[] add a github action to publish to pypi (with UV)

## Add Permit Terraform Provider script to configure Permit.io
[] add a terraform script to configure Permit.io

## Monitoring
[] add monitoring
[] add logging
