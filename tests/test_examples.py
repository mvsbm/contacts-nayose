"""The workflow's own tests: its contract's examples and stage Checks (the studio ran the same)."""

from contacts_nayose.cli import check_examples


def test_examples_and_checks_pass():
    assert check_examples() == []
