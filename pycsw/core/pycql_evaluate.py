from pycql.integrations.sqlalchemy import filters
from pycql.ast import (
    NotConditionNode,
    CombinationConditionNode,
    ComparisonPredicateNode,
    BetweenPredicateNode,
    LikePredicateNode,
    InPredicateNode,
    NullPredicateNode,
    TemporalPredicateNode,
    SpatialPredicateNode,
    BBoxPredicateNode,
    AttributeExpression,
    LiteralExpression,
    ArithmeticExpressionNode,
)

from sqlalchemy import text

from pycsw.core.util import bbox2wktpolygon

def _bbox(lhs, minx, miny, maxx, maxy, crs=4326):
    wkt = bbox2wktpolygon(f'{minx},{miny},{maxx},{maxy}')
    return text(f"query_spatial(wkt_geometry, '{wkt}', 'bbox', 'false') = 'true'")


class FilterEvaluator:
    def __init__(self, field_mapping=None):
        self.field_mapping = field_mapping

    def to_filter(self, node, dbtype='sqlite'):
        to_filter = self.to_filter
        if isinstance(node, NotConditionNode):
            return filters.negate(to_filter(node.sub_node))
        elif isinstance(node, CombinationConditionNode):
            return filters.combine(
                (to_filter(node.lhs), to_filter(node.rhs)), node.op
            )
        elif isinstance(node, ComparisonPredicateNode):
            return filters.runop(
                to_filter(node.lhs), to_filter(node.rhs), node.op,
            )
        elif isinstance(node, BetweenPredicateNode):
            return filters.between(
                to_filter(node.lhs),
                to_filter(node.low),
                to_filter(node.high),
                node.not_,
            )
        elif isinstance(node, LikePredicateNode):
            return filters.like(
                to_filter(node.lhs), to_filter(node.rhs), node.case, node.not_,
            )
        elif isinstance(node, InPredicateNode):
            return filters.runop(
                to_filter(node.lhs),
                [to_filter(sub_node) for sub_node in node.sub_nodes],
                "in",
                node.not_,
            )
        elif isinstance(node, NullPredicateNode):
            return filters.runop(
                to_filter(node.lhs), None, "is_null", node.not_
            )
        elif isinstance(node, TemporalPredicateNode):
            return filters.temporal(to_filter(node.lhs), node.rhs, node.op)
        elif isinstance(node, SpatialPredicateNode):
            return filters.spatial(
                to_filter(node.lhs),
                to_filter(node.rhs),
                node.op,
                to_filter(node.pattern),
                to_filter(node.distance),
                to_filter(node.units),
            )
        elif isinstance(node, BBoxPredicateNode):
            if dbtype == 'sqlite':
                return _bbox(
                    to_filter(node.lhs),
                    to_filter(node.minx),
                    to_filter(node.miny),
                    to_filter(node.maxx),
                    to_filter(node.maxy),
                    to_filter(node.crs),
               )
            else:
                return filters.bbox(
                    to_filter(node.lhs),
                    to_filter(node.minx),
                    to_filter(node.miny),
                    to_filter(node.maxx),
                    to_filter(node.maxy),
                    to_filter(node.crs),
               )
        elif isinstance(node, AttributeExpression):
            return filters.attribute(node.name, self.field_mapping)

        elif isinstance(node, LiteralExpression):
            return node.value

        elif isinstance(node, ArithmeticExpressionNode):
            return filters.runop(
                to_filter(node.lhs), to_filter(node.rhs), node.op
            )

        return node


def to_filter(ast, dbtype, field_mapping=None):
    """ Helper function to translate ECQL AST to Django Query expressions.

        :param ast: the abstract syntax tree
        :param field_mapping: a dict mapping from the filter name to the Django
                              field lookup.
        :param mapping_choices: a dict mapping field lookups to choices.
        :type ast: :class:`Node`
        :returns: a Django query object
        :rtype: :class:`django.db.models.Q`
    """
    return FilterEvaluator(field_mapping).to_filter(ast, dbtype)
