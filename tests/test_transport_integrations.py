from pathlib import Path

from eafix.transport_integrations import (
    TriTransportRouter,
    DummyTransport,
    CsvSpoolTransport,
)


def test_router_failover(tmp_path: Path):
    primary = DummyTransport(should_fail=True)
    secondary = DummyTransport()
    emergency = CsvSpoolTransport(tmp_path / "spool.csv")
    router = TriTransportRouter(primary, secondary, emergency)
    assert router.send({"msg": "hi"}) is True
    assert primary.sent == []
    assert secondary.sent  # message delivered to secondary
