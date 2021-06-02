.. _api:

API
===

Python applications can integrate pycsw into their custom workflows.  This
allows for seamless integate within frameworks such as Flask and Django.

Below are examples of where using the API (as opposed to the default WSGI/CGI
services could be used:

- configuration based on a Python dict, or stored in a database
- downstream request environment / framework (Flask, Django)
- authentication or authorization logic
- forcing CSW version 2.0.2 as default

OARec Flask Example
-------------------

See https://github.com/geopython/pycsw/blob/master/pycsw/wsgi_flask.py for how
to implement a Flask wrapper atop all pycsw supported APIs.  Note the use of
Flask blueprints to enable integration with downstream Flask applications.

Simple Flask blueprint example
------------------------------

.. code-block:: python

  from flask import Flask, redirect

  from pycsw.wsgi_flask import BLUEPRINT as pycsw_blueprint

  app = Flask(__name__, static_url_path='/static')

  app.url_map.strict_slashes = False
  app.register_blueprint(pycsw_blueprint, url_prefix='/oapi')

  @app.route('/')
  def hello_world():
      return "Hello, World!"


In the above example, all pycsw endpoints are made available under ``http://localhost:8000/oapi``.

Simple CSW Flask Example
------------------------

.. code-block:: python

  import logging

  from flask import Flask, request

  from pycsw import __version__ as pycsw_version
  from pycsw.server import Csw

  LOGGER = logging.getLogger(__name__)
  APP = Flask(__name__)
 
  @APP.route('/csw')
  def csw_wrapper():
      """CSW wrapper"""

      LOGGER.info('Running pycsw %s', pycsw_version)

      pycsw_config = some_dict  # really comes from somewhere

      # initialize pycsw
      # pycsw_config: either a ConfigParser object or a dict of
      # the pycsw configuration
      #
      # env: dict of (HTTP) environment (defaults to os.environ)
      # 
      # version: defaults to '3.0.0'
      my_csw = Csw(pycsw_config, request.environ, version='2.0.2')

      # dispatch the request
      http_status_code, response = my_csw.dispatch_wsgi()

      return response, http_status_code, {'Content-type': csw.contenttype}
