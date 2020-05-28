import pytest

from serviceit.server import ServiceServer, Payload

from .test_init import wait


class TestService:

    def test_payload(self):
        input = {"testing": "123"}
        assert str(Payload.encode(input).decode()).replace('"', "'") == str(input).replace('"', "'")

    def test_server_client(self):
        data = []

        def add(d):
            data.append(d)

        server = ServiceServer(add, 0)
        client = server.client()
        client.send(dict(msg="hi"))
        # give it sec to poll and process
        while server.bytes_processed == 0:
            pass
        assert str(data) == str([dict(msg="hi")])
        
    def test_close_client(self):
        data = []

        def add(d):
            data.append(d)

        server = ServiceServer(add, 0)
        client = server.client()
        client.send(dict(msg="hi"))
        assert client.is_open
        client.close()
        assert not client.is_open
        client.send({})

    def test_close_server(self):
        data = []

        def add(d):
            data.append(d)

        server = ServiceServer(add, 0)
        client = server.client()
        client.send(dict(msg="hi"))
        assert server.is_open
        server.close()
        assert not server.is_open
        client.send({})

    def test_str(self):
        server = ServiceServer(lambda s: s, 0)
        client = server.client()
        assert str(server).startswith('ServiceServer') and '127.0.0.1' in str(server)
        assert repr(server).startswith('ServiceServer') and '127.0.0.1' in repr(server)
        assert str(client).startswith('ServiceClient') and 'localhost' in str(client)
        assert repr(client).startswith('ServiceClient') and 'localhost' in repr(client)
    

    def test_receive_none(self):
        slow = int(1e6)
        data = []

        def add(d):
            data.append(d)

        server = ServiceServer(add, 0)
        client = server.client()
        client.send(dict(msg="hi"))
        wait(slow)
        assert client.receive() is None
    
    """
    # TODO
    def test_receive_some(self):
        slow = int(1e6)
        data = []

        def add(d):
            data.append(d)
            return {'success': True}

        server = ServiceServer(add, 0)
        client = server.client()
        client.send(dict(msg="hi"))
        wait(slow)
        assert client.receive() == {'success': True}
    """


if __name__ == "__main__":
    pytest.main()
