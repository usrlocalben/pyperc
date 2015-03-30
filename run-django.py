#!/usr/bin/env python2.7

import os
import sys
import time
import json
import pprint
import httplib
import requests
from urllib import urlencode

from django.conf import settings

#BASE_DIR = os.path.dirname(os.path.dirname(__file__))
BASE_DIR = os.path.dirname(__file__)
print 'the base dir is', BASE_DIR

DEBUG = os.environ.get('DEBUG', 'on') == 'on'
SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(32))
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

settings.configure(
        DEBUG=DEBUG,
        SECRET_KEY=SECRET_KEY,
        ALLOWED_HOSTS=ALLOWED_HOSTS,
        ROOT_URLCONF=__name__,
        MIDDLEWARE_CLASSES=(
#            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
#            'django.middleware.csrf.CsrfViewMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
            ),
        TEMPLATE_DIRS=(
            os.path.join(BASE_DIR, 'templates/'),
            ),
        STATIC_URL='/static/',
        STATICFILES_DIRS=(
            os.path.join(BASE_DIR, 'static'),
            os.path.join(BASE_DIR, 'bower_components'),
            ),
        INSTALLED_APPS=(
            'django.contrib.staticfiles',
            ),
    )

from django.http import HttpResponse
from django.conf.urls import url
from django.core.wsgi import get_wsgi_application
from django.shortcuts import render
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from rest_framework import views
from rest_framework.response import Response


def merge_shallow(a, b):
    out = a
    out.update(b)
    return out

def rpc_get(path, params):
    conn = httplib.HTTPConnection('127.0.0.1:50001')
    query = '?' + urlencode(params) if params else ''
    conn.request('GET', path + query)
    cr = conn.getresponse()
    return json.load(cr)


class EventView(views.APIView):
    permission_classes = []

    def get(self, request):
        since = request.GET.get('since', None)
        limit = request.GET.get('limit', None)

        ignore = (30, 113, 236)

        qparams = {}
        qparams = merge_shallow(qparams, {'since': str(since)} if since else {})
        qparams = merge_shallow(qparams, {'limit': str(limit)} if limit else {})
        result = rpc_get('/events/', qparams)
        raw_events = result['events']

        filtered = (item for item in raw_events if item['code'] not in ignore)
        events = sorted(filtered, key=lambda item: item['id'])

        return Response({'success': True, 'events': events})


class AdapterView(views.APIView):
    permission_classes = []

    def get(self, request):
        pinf = requests.get('http://127.0.0.1:50001/info/').json()
        pinf['success'] = True
        return Response(pinf)


def home(request):
    return render(request, 'dashboard.html', {})


urlpatterns = (
        url(r'^api/events/$', EventView.as_view()),
        url(r'^api/adapter/$', AdapterView.as_view()),
        url(r'^$', home),
        )
urlpatterns = urlpatterns + tuple(staticfiles_urlpatterns())

application = get_wsgi_application()
if __name__ == '__main__':
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

