import httpx

from worker.batch import post_total


def test_post_total():
    transport = httpx.MockTransport(lambda request: httpx.Response(201))
    with httpx.Client(transport=transport, base_url="http://acme") as client:
        assert post_total(client, 330) == 201
