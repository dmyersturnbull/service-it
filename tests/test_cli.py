import pytest

from serviceit import __copyright__
from serviceit import cli

class TestCli:

    def test_cli(self):
        response = cli.info()
        assert __copyright__ in response


if __name__ == "__main__":
    pytest.main()
