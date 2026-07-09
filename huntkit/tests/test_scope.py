import pytest

from huntkit import scope


def test_scope_add_list_remove():
    scope.add("example.com")
    assert scope.list_scope() == ["example.com"]
    assert scope.is_in_scope("EXAMPLE.com")

    scope.remove("example.com")
    assert scope.list_scope() == []


def test_require_in_scope_blocks_unauthorized_targets():
    with pytest.raises(scope.NotInScopeError):
        scope.require_in_scope("not-authorized.example")


def test_require_in_scope_allows_authorized_targets():
    scope.add("authorized.example")
    scope.require_in_scope("authorized.example")  # must not raise
