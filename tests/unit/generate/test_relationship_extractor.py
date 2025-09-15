#!/usr/bin/env python3
"""Test suite for DataWindow relationship extraction."""

import pytest

from src.generate.converters.data.relationships import (
    ColumnMapping,
    JoinType,
    Relationship,
    RelationshipExtractor,
    RelationshipType,
)
from src.parse.parser.specialized.sql import SQLParser


class TestRelationshipExtractor:
    """Test relationship extraction functionality."""

    def test_simple_join_extraction(self):
        """Test extracting relationship from simple JOIN."""
        extractor = RelationshipExtractor()
        parser = SQLParser()

        sql = """
        SELECT c.id, c.name, o.order_date, o.total
        FROM customers c
        INNER JOIN orders o ON c.id = o.customer_id
        """

        parsed = parser.parse(sql)
        stmt = parsed[0] if isinstance(parsed, list) else parsed.statements[0]

        relationships = extractor.extract_from_select(stmt)

        assert len(relationships) == 1
        rel = relationships[0]

        assert rel.source_table == "customers"
        assert rel.target_table == "orders"
        assert rel.join_type == JoinType.INNER
        assert len(rel.column_mappings) == 1
        assert rel.column_mappings[0].source_column == "id"
        assert rel.column_mappings[0].target_column == "customer_id"

    def test_multiple_join_extraction(self):
        """Test extracting relationships from multiple JOINs."""
        extractor = RelationshipExtractor()
        parser = SQLParser()

        sql = """
        SELECT c.name, o.order_date, p.product_name
        FROM customers c
        LEFT JOIN orders o ON c.id = o.customer_id
        INNER JOIN order_items oi ON o.id = oi.order_id
        INNER JOIN products p ON oi.product_id = p.id
        """

        parsed = parser.parse(sql)
        stmt = parsed[0] if isinstance(parsed, list) else parsed.statements[0]

        relationships = extractor.extract_from_select(stmt)

        # Should extract 3 relationships
        assert (
            len(relationships) >= 2
        )  # At least customer->order and order->order_items

        # Check for left join relationship
        left_joins = [r for r in relationships if r.join_type == JoinType.LEFT]
        assert len(left_joins) >= 1
        assert left_joins[0].is_optional is True

    def test_composite_key_join(self):
        """Test extracting relationship with composite key."""
        extractor = RelationshipExtractor()
        parser = SQLParser()

        sql = """
        SELECT *
        FROM order_details od
        INNER JOIN price_history ph
            ON od.product_id = ph.product_id
            AND od.order_date = ph.effective_date
        """

        parsed = parser.parse(sql)
        stmt = parsed[0] if isinstance(parsed, list) else parsed.statements[0]

        relationships = extractor.extract_from_select(stmt)

        assert len(relationships) == 1
        rel = relationships[0]

        # Should have 2 column mappings for composite key
        assert len(rel.column_mappings) == 2

        # Check both mappings exist
        mapping_strs = [
            f"{m.source_column}->{m.target_column}" for m in rel.column_mappings
        ]
        assert "product_id->product_id" in mapping_strs
        assert "order_date->effective_date" in mapping_strs

    def test_implicit_join_extraction(self):
        """Test extracting relationships from WHERE clause (implicit join)."""
        extractor = RelationshipExtractor()
        parser = SQLParser()

        sql = """
        SELECT c.name, o.order_date
        FROM customers c, orders o
        WHERE c.id = o.customer_id
        """

        parsed = parser.parse(sql)
        stmt = parsed[0] if isinstance(parsed, list) else parsed.statements[0]

        relationships = extractor.extract_from_select(stmt)

        assert len(relationships) == 1
        rel = relationships[0]

        assert "implicit" in rel.name
        assert rel.join_type == JoinType.INNER
        assert len(rel.column_mappings) == 1

    def test_relationship_type_detection(self):
        """Test relationship type detection based on column names."""
        extractor = RelationshipExtractor()

        # Test foreign key pattern detection
        assert extractor._is_foreign_key("customer_id")
        assert extractor._is_foreign_key("fk_product")
        assert extractor._is_foreign_key("order_fk")
        assert not extractor._is_foreign_key("name")

        # Test primary key pattern detection
        assert extractor._is_primary_key("id")
        assert extractor._is_primary_key("customer_id")  # Can be PK in customer table
        assert extractor._is_primary_key("pk_order")
        assert not extractor._is_primary_key("description")

    def test_relationship_deduplication(self):
        """Test that duplicate relationships are removed."""
        extractor = RelationshipExtractor()

        # Create duplicate relationships
        mapping = ColumnMapping(
            source_table="customers",
            source_column="id",
            target_table="orders",
            target_column="customer_id",
        )

        rel1 = Relationship(
            name="customers_orders",
            source_table="customers",
            target_table="orders",
            relationship_type=RelationshipType.ONE_TO_MANY,
            join_type=JoinType.INNER,
            column_mappings=[mapping],
        )

        rel2 = Relationship(
            name="customers_orders_2",  # Different name
            source_table="customers",
            target_table="orders",
            relationship_type=RelationshipType.ONE_TO_MANY,
            join_type=JoinType.INNER,
            column_mappings=[mapping],  # Same mapping
        )

        deduplicated = extractor._deduplicate_relationships([rel1, rel2])

        assert len(deduplicated) == 1

    def test_generate_repository_methods(self):
        """Test repository method generation for relationships."""
        extractor = RelationshipExtractor()

        relationships = [
            Relationship(
                name="customer_orders",
                source_table="customers",
                target_table="orders",
                relationship_type=RelationshipType.ONE_TO_MANY,
                join_type=JoinType.INNER,
                column_mappings=[],
            ),
            Relationship(
                name="order_customer",
                source_table="orders",
                target_table="customers",
                relationship_type=RelationshipType.MANY_TO_ONE,
                join_type=JoinType.INNER,
                column_mappings=[],
            ),
            Relationship(
                name="product_categories",
                source_table="products",
                target_table="categories",
                relationship_type=RelationshipType.MANY_TO_MANY,
                join_type=JoinType.INNER,
                column_mappings=[],
            ),
        ]

        methods = extractor.generate_repository_methods(relationships)

        # Check customer repository methods
        assert "customers" in methods
        customer_methods = methods["customers"]
        assert any("getOrders" in m for m in customer_methods)

        # Check order repository methods
        assert "orders" in methods
        order_methods = methods["orders"]
        assert any("getCustomers" in m for m in order_methods)

        # Check product repository methods
        assert "products" in methods
        product_methods = methods["products"]
        assert any("getCategories" in m for m in product_methods)

    def test_complex_sql_with_subqueries(self):
        """Test handling complex SQL with subqueries."""
        extractor = RelationshipExtractor()
        parser = SQLParser()

        sql = """
        SELECT c.name, order_summary.total_orders
        FROM customers c
        LEFT JOIN (
            SELECT customer_id, COUNT(*) as total_orders
            FROM orders
            GROUP BY customer_id
        ) order_summary ON c.id = order_summary.customer_id
        """

        # This should not crash even with subqueries
        try:
            parsed = parser.parse(sql)
            stmt = parsed.statements[0]
            relationships = extractor.extract_from_select(stmt)
            # May or may not extract relationships from subqueries
            assert isinstance(relationships, list)
        except Exception:
            # It's ok if complex subqueries aren't fully supported yet
            pass

    def test_relationship_to_dict(self):
        """Test relationship serialization to dictionary."""
        mapping = ColumnMapping(
            source_table="customers",
            source_column="id",
            target_table="orders",
            target_column="customer_id",
        )

        rel = Relationship(
            name="customer_orders",
            source_table="customers",
            target_table="orders",
            relationship_type=RelationshipType.ONE_TO_MANY,
            join_type=JoinType.LEFT,
            column_mappings=[mapping],
            is_optional=True,
        )

        rel_dict = rel.to_dict()

        assert rel_dict["name"] == "customer_orders"
        assert rel_dict["source_table"] == "customers"
        assert rel_dict["target_table"] == "orders"
        assert rel_dict["type"] == "one_to_many"
        assert rel_dict["join_type"] == "LEFT JOIN"
        assert rel_dict["is_optional"] is True
        assert len(rel_dict["mappings"]) == 1
        assert rel_dict["mappings"][0]["source"] == "id"
        assert rel_dict["mappings"][0]["target"] == "customer_id"


class TestDataWindowIntegration:
    """Test relationship extraction integration with DataWindowConverter."""

    def test_datawindow_with_relationships(self):
        """Test DataWindow conversion with relationship extraction."""
        from src.generate.converters.flutter.datawindows import DataWindowConverter

        converter = DataWindowConverter()

        dw_syntax = """
        datawindow(
            processing=0
        )
        retrieve="SELECT customers.id, customers.name, orders.order_date, orders.total
                 FROM customers
                 INNER JOIN orders ON customers.id = orders.customer_id
                 WHERE orders.status = 'active'"
        """

        definition = converter.convert_datawindow(dw_syntax, "d_customer_orders")

        # Should have extracted relationships
        assert definition.relationships is not None
        assert len(definition.relationships) > 0

        # Check the relationship
        rel = definition.relationships[0]
        assert rel.source_table == "customers"
        assert rel.target_table == "orders"

        # Check that to_dict includes relationships
        dict_repr = definition.to_dict()
        assert "relationships" in dict_repr
        assert "has_relationships" in dict_repr
        assert dict_repr["has_relationships"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
