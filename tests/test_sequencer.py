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

from ast import increment_lineno
from maker_keeper.main import MakerKeeper, IJob
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

    with patch.object(MakerKeeper, "__init__", __init__):
        keeper = MakerKeeper([])
        keeper.process_block()
        lifecycle.terminate.assert_called()


def test_execution():
    sequencer = MagicMock()
    sequencer.getNextJobs = MagicMock(return_value=
        [
            ('0x8f235dD319ef8637964271a9477234f62B02Cb59', True, 0x4e6574776f726b206973206e6f74206d6173746572),
            ('0x17cE6976de56FAf445956e5713b382C28F7A9390', False, 0x4e6574776f726b206973206e6f74206d6173746572),
            ('0xc194673e6157Eca981dEDc1eEf49250aD8055D94', True, 0x4e6574776f726b206973206e6f74206d6173746572)
        ]
    )

    def __init__(self, args: list, **kwargs):
        self.errors = 0
        self.max_errors = 20
        self.network_id = 'network_id'
        self.sequencer = sequencer
        self.jobs = 0

    def execute(self, success: bool, address: str, calldata: str):
        if self.jobs == 0:
            assert success == True
            assert address == '0x8f235dD319ef8637964271a9477234f62B02Cb59'
        if self.jobs == 1:
            assert success == False
            assert address == '0x17cE6976de56FAf445956e5713b382C28F7A9390'
        if self.jobs == 2:
            assert success == True
            assert address == '0xc194673e6157Eca981dEDc1eEf49250aD8055D94'
        assert calldata == 0x4e6574776f726b206973206e6f74206d6173746572
        self.jobs += 1

    with patch.object(MakerKeeper, "__init__", __init__):
        with patch.object(MakerKeeper, "execute", execute):
            keeper = MakerKeeper([])
            keeper.process_block()
            sequencer.getNextJobs.assert_called_with('network_id')
            assert keeper.jobs == 3

