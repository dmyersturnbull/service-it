import pytest
from datetime import datetime
from copy import deepcopy
import json

import serviceit

class TestInit:

    def test_passing(self):
        data = []
        then = datetime.now()
        def process(d):
            data.append(d)
            for i in list(range(0, 100000)): i += 1
        server = serviceit.server(1538, process)
        client = serviceit.client(1538)
        assert server.last_processed is None
        assert client.last_sent is None
        client.send(dict(yes=True))
        client.send(dict(yez=True))
        assert client.payloads_sent == 2
        expected = len(bytes(json.dumps(dict(yes=True)), encoding='utf8'))
        assert client.bytes_sent == expected*2
        # give it sec to poll and process
        while server.payloads_processed() < 2:
            pass
        assert str(data)==str([dict(yes=True)])
        assert server.payloads_processed() == 1
        assert server.last_processed is not None
        assert client.last_sent is not None
        assert then < client.last_sent
        assert then < client.last_sent
        assert client.last_sent < server.last_processed
        client.send(dict(yes=True))
        assert client.payloads_sent == 2
        assert client.bytes_sent == expected*2
        for i in list(range(0, 100000)):
            if i % 100000/10 == 0:
                i += 1
                print(i)
        #while server._service.server.payloads_processed < 2:
        #    pass

        assert str(data)==str([dict(yes=True),dict(yes=True)])
        assert server.payloads_processed == 2


if __name__ == "__main__":
    pytest.main()
