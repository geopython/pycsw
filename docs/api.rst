.. _api:

API
===

Python applications can integrate pycsw into their custom workflows.  This
allows for seamless integate within frameworks like Flask and Django

Below are examples of where using the API (as opposed to the default WSGI/CGI
services could be used:

- configuration based on a Python dict, or stored in a database
- downstream request environment / framework (Flask, Django)
- authentication or authorization logic
- forcing CSW version 2.0.2 as default


Simple Flask Example
--------------------

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
