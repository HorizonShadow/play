from eve import Eve
from eve.io import mongo
from eve.utils import config
from flask import Config, request, send_file, Response
from flask.helpers import get_root_path
from flask.ext.login import current_user
import mimetypes
import os
import re

from play import default_settings
from play.api.auth import SessionAuth


class Validator(mongo.Validator):

    def _validate_roles(self, roles, field, value):
        if not isinstance(roles, list):
            self._error(field, 'Schema error "%s" must be a list' % field)

    def _validate_path(self, path, field, value):
        if bool(path) is True and not os.path.exists(value):
            self._error(field, 'File path must exist')


class Mongo(mongo.Mongo):

    def _datasource_ex(self, resource, query=None, client_projection=None,
                       client_sort=None):
        datasource, query, fields, sort = super()._datasource_ex(
            resource, query=query, client_projection=client_projection, client_sort=client_sort)
        if fields:
            excludes = 0 in fields.values()
            for field_name, schema_field in config.DOMAIN[resource]['schema'].items():
                if 'roles' in schema_field and not current_user.has_role(schema_field['roles']):
                    if excludes:
                        fields[field_name] = 0
                    else:
                        for field in dict(fields):
                            if field.split('.')[0] == field_name:
                                fields.pop(field)

        return datasource, query, fields, sort


class Application(object):

    def __init__(self, settings=None):
        self.settings = Config(get_root_path(__name__))
        self.settings.from_object(default_settings)
        if 'DOMAIN' not in self.settings:
            self.settings['DOMAIN'] = {}
        self._blueprints = []

    def instantiate(self, *args, **kwargs):
        app = Eve(__name__, data=Mongo, validator=Validator, settings=dict(self.settings),
                  auth=SessionAuth, **kwargs)

        for blueprint in self._blueprints:
            for event, function in blueprint.events.__dict__.items():
                if event.startswith('on_'):
                    setattr(app, '{}_{}'.format(event, blueprint.name), function)
            app.register_blueprint(blueprint)
        return app

    def register_blueprint(self, blueprint):
        self._blueprints.append(blueprint)
        self.settings['DOMAIN'][blueprint.name] = blueprint.domain


def send_file_partial(path, etag):
    range_header = request.headers.get('Range', None)
    if not range_header:
        rv = send_file(path)
        rv.set_etag(etag)
        return rv

    size = os.path.getsize(path)
    byte1, byte2 = 0, None

    m = re.search('(\d+)-(\d*)', range_header)
    g = m.groups()

    if g[0]:
        byte1 = int(g[0])
    if g[1]:
        byte2 = int(g[1])

    length = size - byte1
    if byte2 is not None:
        length = byte2 - byte1

    data = None
    with open(path, 'rb') as f:
        f.seek(byte1)
        data = f.read(length)

    rv = Response(
        data, 206, mimetype=mimetypes.guess_type(path)[0],
        direct_passthrough=True)
    rv.set_etag(etag)
    rv.headers.add('Content-Range', 'bytes {0}-{1}/{2}'.format(byte1, byte1 + length - 1, size))
    rv.headers.add('Cache-Control', 'no-cache')
    return rv
