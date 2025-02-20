from base64 import b64decode, b64encode

from django.http import QueryDict
from django.utils.http import urlencode

from corehq.apps.api.util import make_date_filter
from corehq.apps.case_search.filter_dsl import (
    build_filter_from_xpath,
)
from corehq.apps.case_search.exceptions import CaseFilterError
from corehq.apps.es import case_search, filters
from corehq.apps.es import cases as case_es
from dimagi.utils.parsing import FALSE_STRINGS
from .core import UserError, serialize_es_case

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 5000
INDEXED_AFTER = 'indexed_on.gte'
LAST_CASE_ID = 'last_case_id'


def _to_boolean(val):
    return not (val == '' or val.lower() in FALSE_STRINGS)


def _to_int(val, param_name):
    try:
        return int(val)
    except ValueError:
        raise UserError(f"'{val}' is not a valid value for '{param_name}'")


def _make_date_filter(date_filter):
    filter_fn = make_date_filter(date_filter)

    def _exception_converter(param, value):
        """Wrapper to convert ValueError to UserError"""
        try:
            return filter_fn(param, value)
        except ValueError as e:
            raise UserError(str(e))

    return _exception_converter


def _index_filter(identifier, case_id):
    return case_search.reverse_index_case_query(case_id, identifier)


SIMPLE_FILTERS = {
    'external_id': case_search.external_id,
    'case_type': case_es.case_type,
    'owner_id': case_es.owner,
    'case_name': case_es.case_name,
    'closed': lambda val: case_es.is_closed(_to_boolean(val)),
}

# Compound filters take the form `prefix.qualifier=value`
# These filter functions are called with qualifier and value
COMPOUND_FILTERS = {
    'properties': case_search.case_property_query,
    'last_modified': _make_date_filter(case_es.modified_range),
    'server_last_modified': _make_date_filter(case_es.server_modified_range),
    'date_opened': _make_date_filter(case_es.opened_range),
    'date_closed': _make_date_filter(case_es.closed_range),
    'indexed_on': _make_date_filter(case_search.indexed_on),
    'indices': _index_filter,
}


def get_list(domain, params):
    if 'cursor' in params:
        params_string = b64decode(params['cursor']).decode('utf-8')
        params = QueryDict(params_string).dict()
        last_date = params.pop(INDEXED_AFTER, None)
        last_id = params.pop(LAST_CASE_ID, None)
        query = _get_cursor_query(domain, params, last_date, last_id)
    else:
        query = _get_query(domain, params)

    es_result = query.run()
    hits = es_result.hits
    ret = {
        "matching_records": es_result.total,
        "cases": [serialize_es_case(case) for case in hits],
    }

    cases_in_result = len(hits)
    if cases_in_result and es_result.total > cases_in_result:
        cursor = urlencode({**params, **{
            INDEXED_AFTER: hits[-1]["@indexed_on"],
            LAST_CASE_ID: hits[-1]["_id"],
        }})
        ret['next'] = {'cursor': b64encode(cursor.encode('utf-8'))}

    return ret


def _get_cursor_query(domain, params, last_date, last_id):
    query = _get_query(domain, params)
    return query.filter(
        filters.OR(
            filters.AND(
                filters.term('@indexed_on', last_date),
                filters.range_filter('_id', gt=last_id),
            ),
            case_search.indexed_on(gt=last_date),
        )
    )


def _get_query(domain, params):
    page_size = _to_int(params.get('limit', DEFAULT_PAGE_SIZE), 'limit')
    if page_size > MAX_PAGE_SIZE:
        raise UserError(f"You cannot request more than {MAX_PAGE_SIZE} cases per request.")
    query = (case_search.CaseSearchES()
             .domain(domain)
             .size(page_size)
             .sort("@indexed_on")
             .sort("_id", reset_sort=False))
    for key, val in params.items():
        query = query.filter(_get_filter(domain, key, val))
    return query


def _get_filter(domain, key, val):
    if key == 'limit':
        pass
    elif key == 'query':
        return _get_query_filter(domain, val)
    elif key in SIMPLE_FILTERS:
        return SIMPLE_FILTERS[key](val)
    elif '.' in key and key.split(".")[0] in COMPOUND_FILTERS:
        prefix, qualifier = key.split(".", maxsplit=1)
        return COMPOUND_FILTERS[prefix](qualifier, val)
    else:
        raise UserError(f"'{key}' is not a valid parameter.")


def _get_query_filter(domain, query):
    try:
        return build_filter_from_xpath(domain, query)
    except CaseFilterError as e:
        raise UserError(f'Bad query: {e}')
