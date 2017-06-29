from os import path

from django.core.urlresolvers import reverse
from django_dynamic_fixture import G
from rest_framework import status

from main.models import Dataset
from main.tests.api import helpers


class TestPermission(helpers.BaseUserTestCase):
    # TODO
    pass


class TestGenericRecord(helpers.BaseUserTestCase):
    def _more_setup(self):
        self.fields = [
            {
                "name": "Column A",
                "type": "string",
                "constraints": helpers.NOT_REQUIRED_CONSTRAINTS
            },
            {
                "name": "Column B",
                "type": "string",
                "constraints": helpers.REQUIRED_CONSTRAINTS
            }
        ]
        self.data_package = helpers.create_data_package_from_fields(self.fields)
        self.ds = G(Dataset,
                    project=self.project_1,
                    type=Dataset.TYPE_GENERIC,
                    data_package=self.data_package)
        self.url = reverse('api:dataset-upload', kwargs={'pk': self.ds.pk})

    def test_upload_csv_happy_path(self):
        csv_data = [
            ['Column A', 'Column B'],
            ['A1', 'B1'],
            ['A2', 'B2']
        ]
        file_ = helpers.to_csv_file(csv_data)
        client = self.custodian_1_client
        self.assertEquals(0, self.ds.record_queryset.count())
        file_name = path.basename(file_)
        with open(file_) as fp:
            data = {
                'file': fp,
                'strict': True  # upload in strict mode
            }
            resp = client.post(self.url, data=data, format='multipart')
            self.assertEquals(status.HTTP_200_OK, resp.status_code)
            # The records should be saved in order of the row
            qs = self.ds.record_queryset.order_by('pk')
            self.assertEquals(len(csv_data) - 1, qs.count())

            index = 0
            record = qs[index]
            expected_data = {
                'Column A': 'A1',
                'Column B': 'B1',
            }
            self.assertEquals(expected_data, record.data)
            # test that source_info contains the file_name and row_counter
            source_info = record.source_info
            self.assertIsNotNone(source_info)
            expected_info = {
                'file_name': file_name,
                'row': index + 2
            }
            self.assertEqual(source_info, expected_info)

            index = 1
            record = qs[index]
            expected_data = {
                'Column A': 'A2',
                'Column B': 'B2',
            }
            self.assertEquals(expected_data, record.data)
            # test that source_info contains the file_name and row_counter
            source_info = record.source_info
            self.assertIsNotNone(source_info)
            expected_info = {
                'file_name': file_name,
                'row': index + 2
            }
            self.assertEqual(source_info, expected_info)

            self.assertEquals(self.project_1.record_count, len(csv_data) - 1)
            self.assertEquals(self.ds.record_count, len(csv_data) - 1)

    def test_upload_xlsx_happy_path(self):
        csv_data = [
            ['Column A', 'Column B'],
            ['A1', 'B1'],
            ['A2', 'B2']
        ]
        file_ = helpers.to_xlsx_file(csv_data)
        client = self.custodian_1_client
        self.assertEquals(0, self.ds.record_queryset.count())
        file_name = path.basename(file_)
        with open(file_, 'rb') as fp:
            data = {
                'file': fp,
                'strict': True  # upload in strict mode
            }
            resp = client.post(self.url, data=data, format='multipart')
            self.assertEquals(status.HTTP_200_OK, resp.status_code)
            # The records should be saved in order of the row
            qs = self.ds.record_queryset.order_by('pk')
            self.assertEquals(len(csv_data) - 1, qs.count())

            index = 0
            record = qs[index]
            expected_data = {
                'Column A': 'A1',
                'Column B': 'B1',
            }
            self.assertEquals(expected_data, record.data)
            # test that source_info contains the file_name and row_counter
            source_info = record.source_info
            self.assertIsNotNone(source_info)
            expected_info = {
                'file_name': file_name,
                'row': index + 2
            }
            self.assertEqual(source_info, expected_info)

            index = 1
            record = qs[index]
            expected_data = {
                'Column A': 'A2',
                'Column B': 'B2',
            }
            self.assertEquals(expected_data, record.data)
            # test that source_info contains the file_name and row_counter
            source_info = record.source_info
            self.assertIsNotNone(source_info)
            expected_info = {
                'file_name': file_name,
                'row': index + 2
            }
            self.assertEqual(source_info, expected_info)

            self.assertEquals(self.project_1.record_count, len(csv_data) - 1)
            self.assertEquals(self.ds.record_count, len(csv_data) - 1)

    def test_upload_blank_column(self):
        """ Blank column should be ignored"""
        csv_data = [
            ['Column A', '', '   ', 'Column B'],
            ['A1', '', 'something', 'B1'],
            ['A2', '', 'something', 'B2']
        ]
        file_ = helpers.to_xlsx_file(csv_data)
        client = self.custodian_1_client
        self.assertEquals(0, self.ds.record_queryset.count())
        file_name = path.basename(file_)
        with open(file_, 'rb') as fp:
            data = {
                'file': fp,
                'strict': True  # upload in strict mode
            }
            resp = client.post(self.url, data=data, format='multipart')
            self.assertEquals(status.HTTP_200_OK, resp.status_code)
            # The records should be saved in order of the row
            qs = self.ds.record_queryset.order_by('pk')
            self.assertEquals(len(csv_data) - 1, qs.count())
            index = 0
            record = qs[index]
            expected_data = {
                'Column A': 'A1',
                'Column B': 'B1',
            }
            self.assertEquals(expected_data, record.data)
            # test that source_info contains the file_name and row_counter
            source_info = record.source_info
            self.assertIsNotNone(source_info)
            expected_info = {
                'file_name': file_name,
                'row': index + 2
            }
            self.assertEqual(source_info, expected_info)

            index = 1
            record = qs[index]
            expected_data = {
                'Column A': 'A2',
                'Column B': 'B2',
            }
            self.assertEquals(expected_data, record.data)
            # test that source_info contains the file_name and row_counter
            source_info = record.source_info
            self.assertIsNotNone(source_info)
            expected_info = {
                'file_name': file_name,
                'row': index + 2
            }
            self.assertEqual(source_info, expected_info)

            self.assertEquals(self.project_1.record_count, len(csv_data) - 1)
            self.assertEquals(self.ds.record_count, len(csv_data) - 1)
