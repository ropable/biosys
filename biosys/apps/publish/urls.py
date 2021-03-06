from __future__ import absolute_import, unicode_literals, print_function, division

from django.conf.urls import url
from apps.publish.views import data_view, export

publish_urlpatterns = ([
    url(r'^$', data_view.DataView.as_view(), name='data_view'),
    url(r'^data/(?P<pk>\d+)/?$', data_view.JSONDataTableView.as_view(), name='data_json'),
    url(r'^export/(?P<pk>\d+)/?$', export.ExportDataSetView.as_view(), name='data_export'),
    url(r'^export-template/(?P<pk>\d+)/?$', export.ExportTemplateView.as_view(), name='data_export_template')
], 'publish')
