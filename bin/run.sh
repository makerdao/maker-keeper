#!/usr/bin/env bash
/opt/maker/maker-keeper/bin/maker-keeper --primary-eth-rpc-url ${PRIMARY_RPC_URL} --backup-eth-rpc-url ${BACKUP_RPC_URL} --eth-from ${ETHFROM} --eth-private-key ${ETHKEY} --sequencer-address ${SEQUENCER_ADDRESS} --network-id ${NETWORK_ID} --blocknative-api-key ${BLOCKNATIVE_KEY}
