# autoline-keeper
![Build Status](https://github.com/makerdao/autoline-keeper/actions/workflows/.github/workflows/publish.yaml/badge.svg?branch=main)

This repository contains a Keeper that on each block mined checks if there's any debt ceiling change opportunity and executes the transaction to update.
Checking opportunities of debt ceiling change is done by calling the `getNextJob` function of `AutoLineJob` contract (https://etherscan.io/address/0xd3E01B079f0a787Fc2143a43E2Bdd799b2f34d9a).

## Installation

This project uses *Python 3.6.6* and requires *virtualenv* to be installed.

In order to clone the project and install required third-party packages please execute:
```
git clone https://github.com/makerdao/autoline-keeper.git
cd autoline-keeper
git submodule update --init --recursive
./install.sh
```

Can be also installed as a Docker image (makerdao/autoline-keeper)

## Running

```
usage: autoline-keeper [-h] --rpc-url RPC_URL [--rpc-timeout RPC_TIMEOUT]
                       --eth-from ETH_FROM --eth-private-key ETH_PRIVATE_KEY
                       [--autoline-address AUTOLINE_ADDRESS]
                       [--autoline-job-address AUTOLINE_JOB_ADDRESS]
                       [--max-errors MAX_ERRORS] --network-id NETWORK_ID
                       --blocknative-api-key BLOCKNATIVE_API_KEY

optional arguments:
  -h, --help            show this help message and exit
  --rpc-url RPC_URL     JSON-RPC host URL
  --rpc-timeout RPC_TIMEOUT
                        JSON-RPC timeout (in seconds, default: 10)
  --eth-from ETH_FROM   Ethereum account from which to send transactions
  --eth-private-key ETH_PRIVATE_KEY
                        Ethereum private key(s) to use
  --autoline-address AUTOLINE_ADDRESS
                        Address of AutoLine contract (default: 0xC7Bdd1F2B16447dcf3dE045C4a039A60EC2f0ba3)
  --autoline-job-address AUTOLINE_JOB_ADDRESS
                        Address of AutoLineJob contract (default: 0xd3E01B079f0a787Fc2143a43E2Bdd799b2f34d9a)
  --max-errors MAX_ERRORS
                        Maximum number of allowed errors before the keeper
                        terminates (default: 100)
  --network-id NETWORK_ID
                        Unique id of network running autoline keepers (hex encoded)
  --blocknative-api-key BLOCKNATIVE_API_KEY
                        Blocknative key
```

## Sample startup script

```
#!/bin/bash

bin/autoline-keeper \
    --rpc-url https://localhost:8545 \
    --eth-from 0x.... \
    --eth-private-key 5210.... \
    --network-id 0x.... \
    --blocknative-api-key MY-KEY
```


