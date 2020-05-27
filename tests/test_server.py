import pytest

from serviceit.server import ServiceServer


class TestService:
    def test_server(self):
        data = []

        def add(d):
            data.append(d)

        service = ServiceServer(add, 0)
        client = service.client()
        client.send(dict(msg="hi"))
        # give it sec to poll and process
        while service.bytes_processed == 0:
            pass
        assert str(data) == str([dict(msg="hi")])


if __name__ == "__main__":
    pytest.main()
