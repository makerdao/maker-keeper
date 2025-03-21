#!/usr/bin/env bash
/opt/maker/maker-keeper/bin/maker-keeper \
    --primary-eth-rpc-url ${PRIMARY_RPC_URL} \
    --primary-eth-rpc-timeout ${PRIMARY_RPC_TIMEOUT} \
    --backup-eth-rpc-url ${BACKUP_RPC_URL} \
    --backup-eth-rpc-timeout ${BACKUP_RPC_TIMEOUT} \
    --eth-from ${ETHFROM} \
    --eth-private-key ${ETHKEY} \
    --sequencer-address ${SEQUENCER_ADDRESS} \
    --network-id ${NETWORK_ID} \
    --blocknative-api-key ${BLOCKNATIVE_KEY} \
    --max-errors ${MAX_ERRORS}
