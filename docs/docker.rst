Docker
======

Installation
------------

pycsw  provides an official `Docker`_ image which is made available on both the `geopython Docker Hub`_ and our `GitHub Container Registry`_. 

Either ``IMAGE`` can be called with the ``docker`` command, ``geopython/pycsw`` from DockerHub or ``ghcr.io/geophython/pycsw`` from the GitHub Container Registry. Examples below use ``geopython/pygeoapi``. 

Assuming you already have docker installed, you can get a pycsw instance up and running run with the default built-in configuration:

.. code-block:: bash

   docker run -p 8000:8000 geopython/pycsw 
   
   # or
   
   docker run -p 8000:8000 ghcr.io/geopython/pycsw

...then browse to http://localhost:8000
   
Docker will retrieve the pycsw image (if needed) and then
start a new container listening on port 8000.

The default configuration will run pycsw with an sqlite repository backend
loaded with some test data from the CITE test suite. You can use this to take
pycsw for a test drive.


Inspect logs
------------

The default configuration for the docker image outputs logs to stdout. This is
common practice with docker containers and enables the inspection of logs
with the ``docker logs`` command::

    # run a pycsw container in the background
    docker run \
        --name pycsw-test \
        --publish 8000:8000 \
        --detach \
        geopython/pycsw

    # inspect logs
    docker logs pycsw-test

.. note::

   In order to have pycsw logs being sent to standard output you must set
   ``server.logfile=`` in the pycsw configuration file.


Using pycsw-admin.py
--------------------

``pycsw-admin.py`` can be executed on a running container by
using ``docker exec``::

    docker exec -ti <running-container-id> pycsw-admin.py --help


Running custom pycsw containers
-------------------------------

pycsw configuration
^^^^^^^^^^^^^^^^^^^

It is possible to supply a custom configuration file for pycsw as a bind 
mount or as a docker secret (in the case of docker swarm). The configuration 
file is searched at the value of the ``PYCSW_CONFIG`` environmental variable,
which defaults to ``/etc/pycsw/pycsw.yml``. 

Supplying the configuration file via bind mount::

    docker run \
        --name pycsw \
        --detach \
        --volume <path-to-local-pycsw.yml>:/etc/pycsw/pycsw.yml \
        --publish 8000:8000 \
        geopython/pycsw

Supplying the configuration file via docker secrets::

    # first create a docker secret with the pycsw config file
    docker secret create pycsw-config <path-to-local-pycsw.yml>
    docker service create \
        --name pycsw \
        --secret src=pycsw-config,target=/etc/pycsw/pycsw.yml \
        --publish 8000:8000
        geopython/pycsw


sqlite repositories
^^^^^^^^^^^^^^^^^^^

The default database repository is the CITE database that is used for running 
pycsw's test suites. Docker volumes may be used to specify a custom sqlite
database path. It should be mounted under ``/var/lib/pycsw``::

    # first create a docker volume for persisting the database when
    # destroying containers
    docker volume create pycsw-db-data
    docker run \
        --volume db-data:/var/lib/pycsw \
        --detach \
        --publish 8000:8000
        geopython/pycsw


PostgreSQL repositories
^^^^^^^^^^^^^^^^^^^^^^^

Specifying a PostgreSQL repository is just a matter of configuring a custom
pycsw.yml file with the correct specification.

Check `pycsw's github repository`_ for an example of a docker-compose/stack
file that spins up a postgis database together with a pycsw instance.


Setting up a development environment with docker
------------------------------------------------

Working on pycsw's code using docker enables an isolated environment that
helps ensuring reproducibility while at the same time keeping your base
system free from pycsw related dependencies. This can be achieved by:

* Cloning pycsw's repository locally;
* Starting up a docker container with appropriately set up bind mounts. In
  addition, the pycsw docker image supports a ``reload`` flag that turns on
  automatic reloading of the gunicorn web server whenever the code changes;
* Installing the development dependencies by using ``docker exec`` with the
  root user;

The following instructions set up a fully working development environment::

    # clone pycsw's repo
    git clone https://github.com/geopython/pycsw.git

    # start a container for development
    cd pycsw
    docker run \
        --name pycsw-dev \
        --detach \
        --volume ${PWD}/pycsw:/usr/lib/python3.7/site-packages/pycsw \
        --volume ${PWD}/docs:/home/pycsw/docs \
        --volume ${PWD}/LICENSE.txt:/home/pycsw/LICENSE.txt \
        --volume ${PWD}/COMMITTERS.txt:/home/pycsw/COMMITTERS.txt \
        --volume ${PWD}/CONTRIBUTING.rst:/home/pycsw/CONTRIBUTING.rst \
        --volume ${PWD}/pycsw/plugins:/home/pycsw/pycsw/plugins \
        --publish 8000:8000 \
        geopython/pycsw --reload

    # install additional dependencies used in tests and docs
    docker exec \
        -ti \
        --user root \
        pycsw-dev pip3 install -r pycsw/requirements-dev.txt

    # run tests (for example unit tests)
    docker exec -ti pycsw-dev pytest -m unit pycsw

    # build docs
    docker exec -ti pycsw-dev sh -c "cd pycsw/docs && make html"

.. note::

   Please note that the pycsw image only uses python 3.8 and that it also does
   not install pycsw in editable mode. As such it is not possible to
   use ``tox``.

Since the docs directory is bind mounted from your host machine into the
container, after building the docs you may inspect their content visually, for
example by running::

    firefox docs/_build/html/index.html

Kubernetes
==========

For `Kubernetes`_ orchestration, run the following in ``docker/kubernetes``:

.. code-block:: bash

  make up
  make open


Helm
====

For Kubernetes deployment via `Helm`_, run the following in ``docker/helm``:

.. code-block:: bash

  helm install pycsw .
  minikube service pycsw --url


.. _`Docker`: https://www.docker.com
.. _`geopython Docker Hub`: https://hub.docker.com/r/geopython/pycsw
.. _`GitHub Container Registry`: https://github.com/geopython/pycsw/pkgs/container/pycsw
.. _pycsw's github repository: https://github.com/geopython/pycsw/tree/master/docker
.. _Kubernetes: https://kubernetes.io/
.. _Helm: https://helm.sh
