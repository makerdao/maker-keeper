#!/usr/bin/env bash
/opt/maker/autoline-keeper/bin/autoline-keeper --rpc-url ${RPCURL} --eth-from ${ETHFROM} --eth-private-key ${ETHKEY} --autoline-address ${AUTOLINE_ADDRESS} --autoline-job-address ${AUTOLINE_JOB_ADDRESS} --network-id ${NETWORK_ID} --blocknative-api-key ${BLOCKNATIVE_KEY}
