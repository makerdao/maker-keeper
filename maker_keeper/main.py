# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import logging
import sys
import os
import requests
import eth_utils
import time

from io import StringIO
from web3 import Web3, HTTPProvider
from urllib.parse import urlparse

from pymaker.keys import register_private_key
from pymaker.lifecycle import Lifecycle
from pymaker.gas import GeometricGasPrice
from pymaker.keys import register_keys
from pymaker import Contract, Address, Transact

class ExitOnCritical(logging.StreamHandler):
    """Custom class to terminate script execution once
    log records with severity level ERROR or higher occurred"""

    def emit(self, record):
        super().emit(record)
        if record.levelno > logging.ERROR:
            sys.exit(1)

class MakerKeeper:
    """MakerKeeper."""

    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        force=True,
        handlers=[ExitOnCritical()],
    )
    logger = logging.getLogger()
    log_level = logging.getLevelName(os.environ.get("LOG_LEVEL") or "INFO")
    logger.setLevel(log_level)

    def __init__(self, args: list, **kwargs):
        parser = argparse.ArgumentParser(prog='maker-keeper')

        parser.add_argument("--rpc-timeout", type=int, default=10,
                            help="JSON-RPC timeout (in seconds, default: 10)")

        parser.add_argument("--primary-eth-rpc-url", type=str, required=True,
                            help="JSON-RPC host URL")

        parser.add_argument("--primary-eth-rpc-timeout", type=int, default=60,
                            help="JSON-RPC timeout (in seconds, default: 60)")

        parser.add_argument("--backup-eth-rpc-url", type=str, required=True,
                            help="JSON-RPC host URL")

        parser.add_argument("--backup-eth-rpc-timeout", type=int, default=60,
                            help="JSON-RPC timeout (in seconds, default: 60)")

        parser.add_argument("--eth-from", type=str, required=True,
                            help="Ethereum account from which to send transactions")

        parser.add_argument("--eth-private-key", type=str, required=True,
                            help="Ethereum private key(s) to use")

        parser.add_argument("--sequencer-address", type=str,
                            default="0x238b4E35dAed6100C6162fAE4510261f88996EC9",
                            help="Address of Sequencer contract")

        parser.add_argument("--max-errors", type=int, default=100,
                            help="Maximum number of allowed errors before the keeper terminates (default: 100)")

        parser.add_argument('--network-id', type=str, required=True,
                            help="Unique id of network running autoline keepers")

        parser.add_argument('--blocknative-api-key', type=str, required=True,
                            help="Blocknative key")

        self.arguments = parser.parse_args(args)

        self.web3 = None
        self.node_type = None
        self._initialize_blockchain_connection()

        self.max_errors = self.arguments.max_errors
        self.errors = 0

        self.sequencer = Sequencer(self.web3, Address(self.arguments.sequencer_address))

        self.network_id = self.arguments.network_id


    def _initialize_blockchain_connection(self):
        """Initialize connection with Ethereum node."""
        if not self._connect_to_primary_node():
            self.logger.info("Switching to backup node.")
            if not self._connect_to_backup_node():
                self.logger.critical(
                    "Error: Couldn't connect to the primary and backup Ethereum nodes."
                )

    def _connect_to_primary_node(self):
        """Connect to the primary Ethereum node"""
        return self._connect_to_node(
            self.arguments.primary_eth_rpc_url, self.arguments.primary_eth_rpc_timeout, "primary"
        )

    def _connect_to_backup_node(self):
        """Connect to the backup Ethereum node"""
        return self._connect_to_node(
            self.arguments.backup_eth_rpc_url, self.arguments.backup_eth_rpc_timeout, "backup"
        )

    def _connect_to_node(self, rpc_url, rpc_timeout, node_type):
        """Connect to an Ethereum node"""
        try:
            _web3 = Web3(HTTPProvider(rpc_url, {"timeout": rpc_timeout}))
        except (TimeExhausted, Exception) as e:
            self.logger.error(f"Error connecting to Ethereum node: {e}")
            return False
        else:
            if _web3.isConnected():
                self.web3 = _web3
                self.node_type = node_type
                return self._configure_web3()
        return False

    def _configure_web3(self):
        """Configure Web3 connection with private key"""
        try:
            self.web3.eth.defaultAccount = self.arguments.eth_from
            register_private_key(self.web3, self.arguments.eth_private_key)
        except Exception as e:
            self.logger.error(f"Error configuring Web3: {e}")
            return False
        else:
            node_hostname = urlparse(self.web3.provider.endpoint_uri).hostname
            self.logger.info(f"Connected to Ethereum node at {node_hostname}")
            return True

    def main(self):
        """ Initialize the lifecycle and enter into the Keeper Lifecycle controller.
        Each function supplied by the lifecycle will accept a callback function that will be executed.
        The lifecycle.on_block() function will enter into an infinite loop, but will gracefully shutdown
        if it recieves a SIGINT/SIGTERM signal.
        """

        with Lifecycle(self.web3) as lifecycle:
            self.lifecycle = lifecycle
            lifecycle.on_block(self.process_block)

    def process_block(self):
        """ Callback called on each new block. If too many errors, terminate the keeper.
        This is the entrypoint to the Keeper's monitoring logic
        """
        isConnected = self.web3.isConnected()
        logging.info(f'web3 isConntected is: {isConnected}')
        latestBlock = self.web3.eth.block_number
        logging.info(f'current block number: {latestBlock}')

        if self.errors >= self.max_errors:
            logging.error("Number of errors reached max configured, exiting keeper")
            self.lifecycle.terminate()
        else:
            results = self.sequencer.getNextJobs(self.network_id)
            for address, canWork, calldata in results:
                logging.info(f"canWork: {canWork} | Address: {address} | Calldata: {calldata}")
                self.execute(canWork, address, calldata)

    def execute(self, canWork: bool, address: str, calldata: str):
        if canWork:
            gas_strategy = GeometricGasPrice(
                web3=self.web3,
                initial_price=None,
                initial_tip=self.get_initial_tip(self.arguments),
                every_secs=180
            )
            try:
                # Create StringIO object to capture logs from pymaker class
                log_capture_string = StringIO()

                # Set up logging
                ch = logging.StreamHandler(log_capture_string)
                ch.setLevel(logging.WARNING)  # Adjust this to capture the log levels you want
                formatter = logging.Formatter('%(levelname)s - %(message)s')
                ch.setFormatter(formatter)

                # Add custom handler to the logger
                logging.getLogger().addHandler(ch)

                # execute the job
                job = IJob(self.web3, Address(address))
                receipt = job.work(self.network_id, calldata).transact(gas_strategy=gas_strategy)

                # Extract log messages from StringIO object
                log_contents = log_capture_string.getvalue()

                if receipt is not None and receipt.successful:
                    logging.info("Exec on IJob done!")
                # Capture the result of an oracleJob transaction and do not throw an error if it is mined.
                elif receipt is None and "0xe717Ec34b2707fc8c226b34be5eae8482d06ED03" in log_contents and "mined successfully but generated no single log entry" in log_contents:
                    logging.info(f"Exec on IJob done with exceptions in job: {address}")
                # Capture the result of the flapJob transaction and do not throw an error, if the flapJob was not ready to be executed.
                elif receipt is None and "0xc32506E9bB590971671b649d9B8e18CB6260559F" in log_contents and "execution reverted: Vow/insufficient-surplus" in log_contents:
                    logging.info(f"IJob, {address}, will not be executed due to 'Vow/insufficient-surplus'.")
                else:
                    logging.error("Failed to run exec on IJob!")

            except Exception as e:
                logging.error(str(e))
                logging.error("Failed to run exec on IJob!")

        else:
            logging.info(f"No update available. canWork: {canWork}")


    @staticmethod
    def get_initial_tip(arguments) -> int:
        try:
            result = requests.get(
                url='https://api.blocknative.com/gasprices/blockprices',
                headers={
                    'Authorization': arguments.blocknative_api_key
                },
                timeout=15
            )
            if result.ok and result.content:
                confidence_80_tip = result.json().get('blockPrices')[0]['estimatedPrices'][3]['maxPriorityFeePerGas']
                logging.info(f"Using Blocknative 80% confidence tip {confidence_80_tip}")
                return int(confidence_80_tip * GeometricGasPrice.GWEI)
        except Exception as e:
            logging.error(str(e))

        return int(1.5 * GeometricGasPrice.GWEI)


class Sequencer(Contract):
    """A client for the `Sequencer` contract.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `Sequencer` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/Sequencer.abi')

    def __init__(self, web3: Web3, address: Address):
        assert (isinstance(web3, Web3))
        assert (isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    def getNextJobs(self, network_id: str):
        return self._contract.functions.getNextJobs(network_id).call()

    def __repr__(self):
        return f"Sequencer('{self.address}')"


class IJob(Contract):
    """A client for the `IJobInterface` contract.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `IJobInterface` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/IJob.abi')

    def __init__(self, web3: Web3, address: Address):
        assert (isinstance(web3, Web3))
        assert (isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    def work(self, network: str, calldata: str) -> Transact:
        return Transact(self, self.web3, self.abi, self.address, self._contract, "work(bytes32,bytes)", [network, calldata])

    def __repr__(self):
        return f"IJob('{self.address}')"


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s', level=logging.INFO)
    logging.Formatter.converter = time.gmtime
    MakerKeeper(sys.argv[1:]).main()
