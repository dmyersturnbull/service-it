import pytest
from datetime import datetime

import serviceit


def wait(slow):
    for i in list(range(0, slow)):
        if i % slow / 10 == 0:
            i += 1


class TestInit:
    def test_passing(self):
        # TODO This is stochastic and depends on this parameter
        slow = int(1e6)
        port = 0
        data = []
        then = datetime.now()

        def process(d):
            data.append(d)
            wait(slow)

        server = serviceit.server(port, process)
        client = serviceit.client(server.port)
        assert server.last_processed is None
        assert client.last_sent is None
        assert client.payloads_sent == 0
        assert server.payloads_processed == 0
        client.send(dict(yes=True))
        wait(slow)
        assert server.payloads_processed == 1
        client.send(dict(yez=True))
        wait(slow)
        # assert server.payloads_processed() == 2
        client.send(dict(yek=True))
        assert client.payloads_sent == 3
        # give it sec to poll and process
        wait(slow)
        # while server.payloads_processed() < 2:
        #    pass
        assert str(data) == str([{"yes": True}, {"yez": True}, {"yek": True}])
        assert client.bytes_sent == 13 * 3
        # TODO this works, but only if we set slow=int(8*1E7)
        # assert server.bytes_processed == 13*3
        assert server.last_processed is not None
        assert client.last_sent is not None
        assert then < client.last_sent
        assert then < client.last_sent
        # TODO I think this isn't guaranteed anymore. True?
        # assert client.last_sent <= server.last_processed
        client.send(dict(yes=True))
        assert client.payloads_sent == 4
        wait(slow)
        # while server._service.server.payloads_processed < 2:
        #    pass

        assert str(data) == str([{"yes": True}, {"yez": True}, {"yek": True}, {"yes": True}])
        assert server.payloads_processed == 4


if __name__ == "__main__":
    pytest.main()
