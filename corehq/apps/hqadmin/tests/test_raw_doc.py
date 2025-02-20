import json

from django.test import TestCase

from corehq.apps.fixtures.models import Field, LookupTable, LookupTableRow, TypeField

from ..views.data import raw_doc_lookup


class TestRawDocLookup(TestCase):
    maxDiff = None

    def test_lookuptable_raw_doc(self):
        table = make_lookuptable()
        table.save()
        self.addCleanup(table._migration_get_couch_object().delete)
        expected_doc = {
            "model": "fixtures.lookuptable",
            "pk": str(table.id),
            "fields": {
                "domain": "test-domain",
                "is_global": True,
                "tag": "item",
                "fields": [
                    {
                        "name": "qty",
                        "properties": [],
                        "is_indexed": False,
                    }
                ],
                "item_attributes": ["name"],
                "description": "",
            },
        }

        data = raw_doc_lookup(table.id.hex)
        self.assertEqual(json.loads(data["doc"]), expected_doc)
        results = {r.dbname: r for r in data["db_results"]}
        self.assertEqual(results["test_commcarehq__fixtures"].result, "found")

        data = raw_doc_lookup(str(table.id))
        self.assertEqual(json.loads(data["doc"]), expected_doc)

    def test_lookuptablerow_raw_doc(self):
        table = make_lookuptable()
        table.save(sync_to_couch=False)
        row = LookupTableRow(
            domain="test-domain",
            table=table,
            fields={"qty": [Field(value="2")]},
            item_attributes={"name": "iron"},
            sort_key=0,
        )
        row.save()
        self.addCleanup(row._migration_get_couch_object().delete)
        expected_doc = {
            "model": "fixtures.lookuptablerow",
            "pk": str(row.id),
            "fields": {
                "table": str(table.id),
                "domain": "test-domain",
                "fields": {
                    "qty": [{"value": "2", "properties": {}}],
                },
                "item_attributes": {"name": "iron"},
                "sort_key": 0,
            },
        }

        data = raw_doc_lookup(row.id.hex)
        self.assertEqual(json.loads(data["doc"]), expected_doc)
        results = {r.dbname: r for r in data["db_results"]}
        self.assertEqual(results["test_commcarehq__fixtures"].result, "found")

        data = raw_doc_lookup(str(row.id))
        self.assertEqual(json.loads(data["doc"]), expected_doc)

    def test_raw_doc_with_invalid_uuid(self):
        data = raw_doc_lookup("abcxyz")
        self.assertNotIn("doc", data)
        self.assertEqual({r.result for r in data["db_results"]}, {"missing"})


def make_lookuptable():
    return LookupTable(
        domain='test-domain',
        is_global=True,
        tag='item',
        fields=[TypeField(name='qty')],
        item_attributes=['name'],
    )
