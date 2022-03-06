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
import requests
import eth_utils

from web3 import Web3, HTTPProvider
from pymaker.keys import register_private_key
from pymaker.lifecycle import Lifecycle
from pymaker.gas import GeometricGasPrice
from pymaker import Contract, Address, Transact


class AutolineKeeper:
    """AutolineKeeper."""

    logger = logging.getLogger()

    def __init__(self, args: list, **kwargs):
        parser = argparse.ArgumentParser(prog='autoline-keeper')

        parser.add_argument("--rpc-url", type=str, required=True,
                            help="JSON-RPC host URL")

        parser.add_argument("--rpc-timeout", type=int, default=10,
                            help="JSON-RPC timeout (in seconds, default: 10)")

        parser.add_argument("--eth-from", type=str, required=True,
                            help="Ethereum account from which to send transactions")

        parser.add_argument("--eth-private-key", type=str, required=True,
                            help="Ethereum private key(s) to use")

        parser.add_argument("--sequencer-address", type=str,
                            default="0x9566eB72e47E3E20643C0b1dfbEe04Da5c7E4732",
                            help="Address of Sequencer contract")

        parser.add_argument("--max-errors", type=int, default=100,
                            help="Maximum number of allowed errors before the keeper terminates (default: 100)")

        parser.add_argument('--network-id', type=str, required=True,
                            help="Unique id of network running autoline keepers")

        parser.add_argument('--blocknative-api-key', type=str, required=True,
                            help="Blocknative key")

        self.arguments = parser.parse_args(args)

        self.web3 = kwargs['web3'] if 'web3' in kwargs else Web3(HTTPProvider(endpoint_uri=self.arguments.rpc_url,
                                                                              request_kwargs={"timeout": self.arguments.rpc_timeout}))
        self.web3.eth.defaultAccount = self.arguments.eth_from
        register_private_key(self.web3, self.arguments.eth_private_key)

        self.max_errors = self.arguments.max_errors
        self.errors = 0

        self.autoline_job = AutoLineJob(self.web3, Address(self.arguments.sequencer_address))

        self.network_id = self.arguments.network_id

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
        if self.errors >= self.max_errors:
            logging.error("Number of errors reached max configured, exiting keeper")
            self.lifecycle.terminate()
        else:
            results = self.autoline_job.getNextJobs(self.network_id)
            for address, success, calldata in results:
                logging.info(f"Success: {success} | Address: {address} | Calldata: {calldata}")
                self.execute(success, address, calldata)

    def execute(self, success: bool, address: str, calldata: str):
        if success and self.autoline.address.address.lower() == address.lower():
            gas_strategy = GeometricGasPrice(
                web3=self.web3,
                initial_price=None,
                initial_tip=self.get_initial_tip(self.arguments),
                every_secs=180
            )
            try:
                job = AutoLine(self.web3, Address(address))
                receipt = job.get_transact(calldata).transact(gas_strategy=gas_strategy)
                if receipt is not None and receipt.successful:
                    logging.info("Exec on Autoline done!")
                else:
                    logging.error("Failed to run exec on Autoline!")

            except Exception as e:
                logging.error(str(e))
                logging.error("Failed to run exec on Autoline!")

        else:
            logging.info("No update available")


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


class AutoLineJob(Contract):
    """A client for the `AutolineJob` contract.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `AutolineJob` contract.
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
        return f"AutoLineJob('{self.address}')"


class AutoLine(Contract):
    """A client for the `AutoLine` contract.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `AutoLine` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/IJob.abi')

    def __init__(self, web3: Web3, address: Address):
        assert (isinstance(web3, Web3))
        assert (isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    def get_transact(self, calldata: str) -> Transact:
        return Transact(self, self.web3, self.abi, self.address, self._contract, "work(bytes32,bytes)", calldata)

    def __repr__(self):
        return f"AutoLine('{self.address}')"


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s', level=logging.INFO)
    AutolineKeeper(sys.argv[1:]).main()
