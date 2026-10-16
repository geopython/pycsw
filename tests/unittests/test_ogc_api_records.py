"""Unit tests for OGC API - Records record generation."""

import pytest

from pycsw.ogc.api.records import record2json

pytestmark = pytest.mark.unit

TOPIC_SCHEME = 'https://standards.iso.org/iso/19139/resources/gmxCodelists.xml#MD_TopicCategoryCode'


class Record:
    identifier = 'record-1'
    title = 'Title'
    typename = 'gmd:MD_Metadata'
    metadata_type = 'application/xml'
    type = 'dataset'

    def __init__(self, topicategory):
        self.topicategory = topicategory

    def __getattr__(self, name):
        return None


def topic_concepts(topicategory):
    record = record2json(Record(topicategory), 'http://localhost/pycsw', 'metadata:main')
    themes = record['properties'].get('themes', [])
    return [concept['id'] for theme in themes if theme['scheme'] == TOPIC_SCHEME
            for concept in theme['concepts']]


@pytest.mark.parametrize('topicategory, expected', [
    ('environment', ['environment']),
    # stored comma-separated by repositories: one concept each
    ('climatologyMeteorologyAtmosphere,environment',
     ['climatologyMeteorologyAtmosphere', 'environment']),
    ('oceans, environment,', ['oceans', 'environment']),
    (['oceans', 'environment'], ['oceans', 'environment']),
])
def test_topic_categories_are_one_concept_each(topicategory, expected):
    assert topic_concepts(topicategory) == expected
