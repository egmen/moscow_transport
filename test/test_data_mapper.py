import unittest
import json
import os
import sys
from custom_components.moscow_transport.data_mapper import get_closest_route

json_file = open(os.path.join(
    sys.path[0], 'response_fixture.json'), encoding='utf-8')
test_json = json.load(json_file)


class DataMapperTest(unittest.TestCase):
    def test_closest_route_all(self):
        res = get_closest_route(test_json)

        self.assertTupleEqual(res, ('688', 140, 1))

    def test_closest_route_733(self):
        res = get_closest_route(test_json, ['733к'])

        self.assertTupleEqual(res, ('733к', 27534, 0))

    def test_closest_route_688(self):
        res = get_closest_route(test_json, ['733к', '733'])

        self.assertTupleEqual(res, ('733', 299, 1))

    def test_no_closest_route(self):
        res = get_closest_route(test_json, ['absent_route'])

        self.assertTupleEqual(res, ())

    def xtest_success_stop_data(self):

        # https://moscowtransport.app/api/stop_v2/a6477b89-72c7-4359-8286-3f148874d653
        stop_data = api.get_stop_info(
            'a6477b89-72c7-4359-8286-3f148874d653')

        self.assertEqual(stop_data['name'], 'Метро "Кунцевская"')
        self.assertEqual(
            stop_data['id'], 'a6477b89-72c7-4359-8286-3f148874d653')

    def xtest_fail_no_data(self):

        with self.assertRaisesRegex(Exception, 'Нет остановки с stop_id=some_absent_uuid'):
            api.get_stop_info('some_absent_uuid')
