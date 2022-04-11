from django.core.management import call_command
from django.test import SimpleTestCase

from corehq.apps.es.tests.utils import es_test
from corehq.elastic import get_es_new
from corehq.pillows.mappings.sms_mapping import SMS_INDEX_INFO  # any valid index will do
from pillowtop.es_utils import initialize_index_and_mapping


@es_test(index=SMS_INDEX_INFO, setup_class=True)
class TestUpdateEsMapping(SimpleTestCase):
    """Guard against management command argument changes breaking the
    `update_es_mapping` migration utility in the future."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.index = SMS_INDEX_INFO.index
        cls.es = get_es_new()
        cls.drop_index()
        initialize_index_and_mapping(cls.es, SMS_INDEX_INFO)

    @classmethod
    def tearDownClass(cls):
        cls.drop_index()
        super().tearDownClass()

    @classmethod
    def drop_index(cls):
        if cls.es.indices.exists(cls.index):
            cls.es.indices.delete(cls.index)

    def test_update_es_mapping(self):
        """Ensure the management command succeeds"""
        call_command("update_es_mapping", self.index, noinput=True)

    def test_update_es_mapping_quite(self):
        """Ensure the management command succeeds with --quiet"""
        call_command("update_es_mapping", self.index, "--quiet", noinput=True)
