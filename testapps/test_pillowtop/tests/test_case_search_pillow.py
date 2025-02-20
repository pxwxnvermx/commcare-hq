import uuid
from unittest.mock import MagicMock, patch

from django.test import TestCase

from pillowtop.es_utils import initialize_index_and_mapping

from corehq.apps.case_search.const import SPECIAL_CASE_PROPERTIES_MAP
from corehq.apps.case_search.exceptions import CaseSearchNotEnabledException
from corehq.apps.case_search.models import CaseSearchConfig
from corehq.apps.change_feed import topics
from corehq.apps.change_feed.consumer.feed import (
    change_meta_from_kafka_message,
)
from corehq.apps.change_feed.tests.utils import get_test_kafka_consumer
from corehq.apps.change_feed.topics import get_topic_offset
from corehq.apps.data_dictionary.models import CaseProperty, CaseType
from corehq.apps.es import CaseSearchES
from corehq.apps.es.tests.utils import es_test
from corehq.elastic import get_es_new
from corehq.form_processor.tests.utils import FormProcessorTestUtils
from corehq.pillows.case import get_case_pillow
from corehq.pillows.case_search import (
    CaseSearchReindexerFactory,
    delete_case_search_cases,
    domains_needing_search_index,
)
from corehq.pillows.mappings.case_search_mapping import (
    CASE_SEARCH_INDEX,
    CASE_SEARCH_INDEX_INFO,
)
from corehq.util.elastic import ensure_index_deleted
from corehq.util.test_utils import create_and_save_a_case, flag_enabled


@es_test
class CaseSearchPillowTest(TestCase):

    domain = 'meereen'
    case_type = 'my_case_type'

    def setUp(self):
        super(CaseSearchPillowTest, self).setUp()
        FormProcessorTestUtils.delete_all_cases()
        self.elasticsearch = get_es_new()
        self.pillow = get_case_pillow(skip_ucr=True)
        ensure_index_deleted(CASE_SEARCH_INDEX)

        # Bootstrap ES
        initialize_index_and_mapping(get_es_new(), CASE_SEARCH_INDEX_INFO)

    def tearDown(self):
        ensure_index_deleted(CASE_SEARCH_INDEX)
        CaseSearchConfig.objects.all().delete()
        super(CaseSearchPillowTest, self).tearDown()

    def test_case_search_reindex_by_domain(self):
        """
        Tests reindexing for a particular domain only
        """
        other_domain = "yunkai"
        CaseSearchConfig.objects.get_or_create(pk=other_domain, enabled=True)
        domains_needing_search_index.clear()

        desired_case = self._make_case(domain=other_domain)
        undesired_case = self._make_case(domain=self.domain)  # noqa

        with self.assertRaises(CaseSearchNotEnabledException):
            CaseSearchReindexerFactory(domain=self.domain).build().reindex()

        CaseSearchReindexerFactory(domain=other_domain).build().reindex()
        self._assert_case_in_es(other_domain, desired_case)

    def test_delete_case_search_cases(self):
        """
        Tests that cases are correctly removed from the es index
        """
        other_domain = "braavos"
        self._bootstrap_cases_in_es_for_domain(self.domain)
        case = self._bootstrap_cases_in_es_for_domain(other_domain)

        with self.assertRaises(TypeError):
            delete_case_search_cases(None)
        with self.assertRaises(TypeError):
            delete_case_search_cases({})

        # delete cases from one domain
        delete_case_search_cases(self.domain)

        # make sure the other domain's cases are still there
        self._assert_case_in_es(other_domain, case)

        # delete other domains cases
        delete_case_search_cases(other_domain)

        # make sure nothing is left
        self._assert_index_empty()

    def test_sql_case_search_pillow(self):
        consumer = get_test_kafka_consumer(topics.CASE_SQL)
        # have to get the seq id before the change is processed
        kafka_seq = self._get_kafka_seq()
        case = self._make_case(case_properties={'something': 'something_else'})

        # confirm change made it to kafka
        message = next(consumer)
        change_meta = change_meta_from_kafka_message(message.value)
        self.assertEqual(case.case_id, change_meta.document_id)
        self.assertEqual(self.domain, change_meta.domain)

        # enable case search for domain
        with patch('corehq.pillows.case_search.domain_needs_search_index',
                   new=MagicMock(return_value=True)) as fake_case_search_enabled_for_domain:
            # send to elasticsearch
            self.pillow.process_changes(since=kafka_seq, forever=False)
            fake_case_search_enabled_for_domain.assert_called_with(self.domain)

        self._assert_case_in_es(self.domain, case)

    def _get_kafka_seq(self):
        return get_topic_offset(topics.CASE_SQL)

    @flag_enabled('USH_CASE_CLAIM_UPDATES')
    def test_geopoint_property(self):
        CaseSearchConfig.objects.get_or_create(pk=self.domain, enabled=True)
        domains_needing_search_index.clear()
        self._make_data_dictionary(gps_properties=['coords', 'short_coords', 'other_coords'])
        case = self._make_case(case_properties={
            'coords': '-33.8561 151.2152 0 0',
            'short_coords': '-33.8561 151.2152',
            'other_coords': '42 Wallaby Way',
            'not_coords': '-33.8561 151.2152 0 0',
        })
        CaseSearchReindexerFactory(domain=self.domain).build().reindex()
        self.elasticsearch.indices.refresh(CASE_SEARCH_INDEX)

        es_case = CaseSearchES().doc_id(case.case_id).run().hits[0]
        self.assertEqual(
            self._get_prop(es_case['case_properties'], 'coords'),
            {
                'key': 'coords',
                'value': '-33.8561 151.2152 0 0',
                'geopoint_value': {'lat': -33.8561, 'lon': 151.2152},
            },
        )
        self.assertEqual(
            self._get_prop(es_case['case_properties'], 'short_coords'),
            {
                'key': 'short_coords',
                'value': '-33.8561 151.2152',
                'geopoint_value': {'lat': -33.8561, 'lon': 151.2152},
            },
        )
        self.assertEqual(
            self._get_prop(es_case['case_properties'], 'other_coords'),
            # The value here isn't a valid geopoint
            {'key': 'other_coords', 'value': '42 Wallaby Way', 'geopoint_value': None},
        )
        self.assertEqual(
            self._get_prop(es_case['case_properties'], 'not_coords'),
            # This isn't a geopoint property in the data dictionary
            {'key': 'not_coords', 'value': '-33.8561 151.2152 0 0'},
        )

    def _make_data_dictionary(self, gps_properties):
        case_type = CaseType.objects.create(name=self.case_type, domain=self.domain)
        for prop in gps_properties:
            CaseProperty.objects.create(case_type=case_type, data_type="gps", name=prop)

    @staticmethod
    def _get_prop(case_properties, key):
        return [prop for prop in case_properties if prop['key'] == key][0]

    def _make_case(self, domain=None, case_properties=None):
        # make a case
        case_id = uuid.uuid4().hex
        case_name = 'case-name-{}'.format(uuid.uuid4().hex)
        if domain is None:
            domain = self.domain
        case = create_and_save_a_case(domain, case_id, case_name, case_properties, self.case_type)
        return case

    def _assert_case_in_es(self, domain, case):
        # confirm change made it to elasticsearch
        self.elasticsearch.indices.refresh(CASE_SEARCH_INDEX)
        results = CaseSearchES().run()
        self.assertEqual(1, results.total)
        case_doc = results.hits[0]

        self.assertEqual(domain, case_doc['domain'])
        self.assertEqual(case.case_id, case_doc['_id'])
        self.assertEqual(case.name, case_doc['name'])
        # Confirm change contains case_properties
        self.assertItemsEqual(list(case_doc['case_properties'][0]), ['key', 'value'])
        for case_property in case_doc['case_properties']:
            key = case_property['key']
            try:
                self.assertEqual(
                    SPECIAL_CASE_PROPERTIES_MAP[key].value_getter(case.to_json()),
                    case_property['value'],
                )
            except KeyError:
                self.assertEqual(case.get_case_property(key), case_property['value'])

    def _assert_index_empty(self):
        self.elasticsearch.indices.refresh(CASE_SEARCH_INDEX)
        results = CaseSearchES().run()
        self.assertEqual(0, results.total)

    def _bootstrap_cases_in_es_for_domain(self, domain):
        case = self._make_case(domain)
        with patch('corehq.pillows.case_search.domains_needing_search_index',
                   MagicMock(return_value=[domain])):
            CaseSearchReindexerFactory(domain=domain).build().reindex()
        return case
