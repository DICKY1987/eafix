from core.constraint_repository import TradingConstraintRepository, TradingConstraint


def test_constraint_repository_query_and_evaluate(tmp_path):
    db_path = tmp_path / "constraints.db"
    repo = TradingConstraintRepository(str(db_path))

    constraint = TradingConstraint(
        id=None,
        name="max_active_trades",
        constraint_type="system_health",
        metric="active_trades",
        operator="le",
        threshold=5,
        tags={"constraint_type": "system_health"},
        severity="WARNING",
    )
    repo.add_constraint(constraint)

    constraints = repo.query_constraints({"constraint_type": "system_health"})
    assert constraints and constraints[0].name == "max_active_trades"

    metrics = {"active_trades": 3}
    results = repo.evaluate(metrics, {"constraint_type": "system_health"})
    assert results["max_active_trades"] is True

    metrics_bad = {"active_trades": 10}
    results_bad = repo.evaluate(metrics_bad, {"constraint_type": "system_health"})
    assert results_bad["max_active_trades"] is False

    repo.close()
