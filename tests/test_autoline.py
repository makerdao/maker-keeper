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

from autoline_keeper.main import AutolineKeeper, AutoLineJob
from unittest.mock import MagicMock, patch
from pymaker.lifecycle import Lifecycle
from pymaker import Address
from web3 import Web3


def test_exit_on_error():
    lifecycle = Lifecycle()
    lifecycle.terminate = MagicMock()

    def __init__(self, args: list, **kwargs):
        self.errors = 21
        self.max_errors = 20
        self.lifecycle = lifecycle

    with patch.object(AutolineKeeper, "__init__", __init__):
        keeper = AutolineKeeper([])
        keeper.process_block()
        lifecycle.terminate.assert_called()


def test_no_execution():
    autoline_job = MagicMock()
    autoline_job.getNextJob = MagicMock(return_value=[
        False,
        "0x0000000000000000000000000000000000000000",
        "b'No ilks ready'"
    ])

    transact = MagicMock()
    autoline = MagicMock()
    autoline.transact = MagicMock(return_value=transact)

    def __init__(self, args: list, **kwargs):
        self.errors = 0
        self.max_errors = 20
        self.network_id = 'network_id'
        self.autoline_job = autoline_job
        self.autoline = autoline

    with patch.object(AutolineKeeper, "__init__", __init__):
        keeper = AutolineKeeper([])
        keeper.process_block()
        autoline_job.getNextJob.assert_called_with('network_id')
        autoline.transact.assert_not_called()


def test_execution():
    autoline_job = MagicMock()
    autoline_job.getNextJob = MagicMock(return_value=[
        True,
        "0xc7bdd1f2b16447dcf3de045c4a039a60ec2f0ba3",
        "MATIC-A"
    ])

    transact = MagicMock()
    autoline = MagicMock()
    autoline.get_transact = MagicMock(return_value=transact)
    autoline.address = Address('0xc7bdd1f2b16447dcf3de045c4a039a60ec2f0ba3')

    def __init__(self, args: list, **kwargs):
        self.errors = 0
        self.max_errors = 20
        self.network_id = 'network_id'

        self.arguments = {}

        self.web3 = Web3()
        self.autoline_job = autoline_job
        self.autoline = autoline

    with patch.object(AutolineKeeper, "__init__", __init__):
        keeper = AutolineKeeper([])
        keeper.process_block()
        autoline_job.getNextJob.assert_called_with('network_id')
        autoline.get_transact.assert_called_with('MATIC-A')
        transact.transact.assert_called()
