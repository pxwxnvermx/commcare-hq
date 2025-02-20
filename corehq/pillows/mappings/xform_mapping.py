from corehq.apps.es.forms import ElasticForm
from corehq.pillows.core import DATE_FORMATS_STRING, DATE_FORMATS_ARR
from corehq.pillows.mappings.const import NULL_VALUE
from corehq.util.elastic import prefix_for_tests
from pillowtop.es_utils import ElasticsearchIndexInfo, XFORM_HQ_INDEX_NAME

XFORM_INDEX = ElasticForm.index_name
XFORM_ES_TYPE = ElasticForm.type
XFORM_ALIAS = prefix_for_tests("xforms")

XFORM_MAPPING = {
    "_meta": {
        "created": "2013-08-13"
    },
    "date_detection": False,
    "date_formats": DATE_FORMATS_ARR,  # for parsing the explicitly defined dates
    "dynamic": False,
    "properties": {
        "#export_tag": {
            "index": "not_analyzed",
            "type": "string"
        },
        "@uiVersion": {
            "type": "string"
        },
        "@version": {
            "type": "string"
        },
        "__retrieved_case_ids": {
            "index": "not_analyzed",
            "type": "string"
        },
        "_attachments": {
            "dynamic": False,
            "type": "object"
        },
        "app_id": {
            "index": "not_analyzed",
            "type": "string"
        },
        "backend_id": {
            "index": "not_analyzed",
            "type": "string"
        },
        "build_id": {
            "index": "not_analyzed",
            "type": "string"
        },
        "doc_type": {
            "type": "string"
        },
        "domain": {
            "fields": {
                "domain": {
                    "index": "analyzed",
                    "type": "string"
                },
                "exact": {
                    # exact is full text string match - hyphens get parsed in standard
                    # analyzer
                    # in queries you can access by domain.exact
                    "index": "not_analyzed",
                    "type": "string"
                }
            },
            "type": "multi_field"
        },
        "external_blobs": {
            "dynamic": False,
            "type": "object"
        },
        "form": {
            "dynamic": False,
            "properties": {
                "#type": {
                    "index": "not_analyzed",
                    "type": "string"
                },
                "@name": {
                    "index": "not_analyzed",
                    "type": "string"
                },
                "case": {
                    "dynamic": False,
                    "properties": {
                        # Note, the case_id method here assumes single case
                        # properties within a form.
                        # In order to support multi case properties, a dynamic
                        # template needs to be added along with fundamentally
                        # altering case queries
                        "@case_id": {
                            "index": "not_analyzed",
                            "type": "string"
                        },
                        "@date_modified": {
                            "format": DATE_FORMATS_STRING,
                            "type": "date"
                        },
                        "@user_id": {
                            "index": "not_analyzed",
                            "type": "string"
                        },
                        "@xmlns": {
                            "index": "not_analyzed",
                            "type": "string"
                        },
                        "case_id": {
                            "index": "not_analyzed",
                            "type": "string"
                        },
                        "date_modified": {
                            "format": DATE_FORMATS_STRING,
                            "type": "date"
                        },
                        "user_id": {
                            "index": "not_analyzed",
                            "type": "string"
                        },
                        "xmlns": {
                            "index": "not_analyzed",
                            "type": "string"
                        }
                    }
                },
                "meta": {
                    "dynamic": False,
                    "properties": {
                        "appVersion": {
                            "index": "not_analyzed",
                            "type": "string"
                        },
                        "app_build_version": {
                            "index": "not_analyzed",
                            "type": "string"
                        },
                        "commcare_version": {
                            "index": "not_analyzed",
                            "type": "string"
                        },
                        "deviceID": {
                            "index": "not_analyzed",
                            "type": "string"
                        },
                        "geo_point": {
                            "geohash": True,
                            "geohash_precision": "10m",
                            "geohash_prefix": True,
                            "lat_lon": True,
                            "type": "geo_point"
                        },
                        "instanceID": {
                            "index": "not_analyzed",
                            "type": "string"
                        },
                        "timeEnd": {
                            "format": DATE_FORMATS_STRING,
                            "type": "date"
                        },
                        "timeStart": {
                            "format": DATE_FORMATS_STRING,
                            "type": "date"
                        },
                        "userID": {
                            "index": "not_analyzed",
                            "null_value": NULL_VALUE,
                            "type": "string"
                        },
                        "username": {
                            "index": "not_analyzed",
                            "type": "string"
                        }
                    }
                }
            }
        },
        "initial_processing_complete": {
            "type": "boolean"
        },
        "inserted_at": {
            "format": DATE_FORMATS_STRING,
            "type": "date"
        },
        "partial_submission": {
            "type": "boolean"
        },
        "path": {
            "index": "not_analyzed",
            "type": "string"
        },
        "received_on": {
            "format": DATE_FORMATS_STRING,
            "type": "date"
        },
        "server_modified_on": {
            "format": DATE_FORMATS_STRING,
            "type": "date"
        },
        "submit_ip": {
            "type": "ip"
        },
        "user_type": {
            "index": "not_analyzed",
            "null_value": NULL_VALUE,
            "type": "string"
        },
        "xmlns": {
            "fields": {
                "exact": {
                    "index": "not_analyzed",
                    "type": "string"
                },
                "xmlns": {
                    "index": "analyzed",
                    "type": "string"
                }
            },
            "type": "multi_field"
        }
    }
}

if ElasticForm.settings.get("DISABLE_ALL"):
    XFORM_MAPPING["_all"] = {"enabled": False}

XFORM_INDEX_INFO = ElasticsearchIndexInfo(
    index=XFORM_INDEX,
    alias=XFORM_ALIAS,
    type=XFORM_ES_TYPE,
    mapping=XFORM_MAPPING,
    hq_index_name=XFORM_HQ_INDEX_NAME,
)
