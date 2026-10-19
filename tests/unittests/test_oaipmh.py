"""OAI-PMH from / until as CQL constraints for repositories without a database."""

from types import SimpleNamespace

import pytest
from pygeofilter import ast
from pygeofilter.parsers.ecql import parse

from pycsw.oaipmh import OAIPMH

pytestmark = pytest.mark.unit


def constraint(**kvp):
    oaipmh = OAIPMH(SimpleNamespace(namespaces={}), {})
    kvp = {'verb': 'ListRecords', 'metadataprefix': 'iso19139', **kvp}
    return oaipmh.request(kvp).get('constraint')


@pytest.mark.parametrize('kvp, expected', [
    ({'from': '2024-01-31'}, [('>=', '2024-01-31')]),
    ({'until': '2024-01-31'}, [('<=', '2024-01-31T23:59:59Z')]),
    ({'from': '2024-01-01T06:00:00Z', 'until': '2024-01-31T18:00:00Z'},
     [('>=', '2024-01-01T06:00:00Z'), ('<=', '2024-01-31T18:00:00Z')]),
])
def test_dates_are_compared_as_values(kvp, expected):
    node = parse(constraint(**kvp))
    comparisons = [node.lhs, node.rhs] if isinstance(node, ast.And) else [node]
    assert [(c.op.value, c.rhs) for c in comparisons] == expected
    assert all(c.lhs == ast.Attribute('dc:date') for c in comparisons)


@pytest.mark.parametrize('value', ['2024-01', '2024-01-31T12:00Z', "2024-01-31' or 'a'='a"])
def test_invalid_dates_build_no_constraint(value):
    assert constraint(**{'from': value}) is None
    assert constraint(until=value) is None
