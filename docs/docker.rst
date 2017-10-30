Docker
======

pycsw is available as a Docker image. The image is hosted on the docker hub
at geopython/pyycsw. It can be obtained by running:

docker pull geopython/pycsw:<pycsw-version>

The ``latest`` tag is also availabe and corresponds to the most up to date 
master branch.

pycsw.cfg
+++++++++

It is possible to supply a custom configuration file for pycsw as a bind 
mount or as a docker secret (in the case of docker swarm). The configuration 
file is searched at the value of the ``PYCSW_CONFIG`` environmental variable,
which defaults to ``/etc/pycsw/pycsw.cfg``. 

Supplying the configuration file via bind mount:

docker run \
    --name pycsw \
    --dettach \
    -v <path-to-pycsw.cfg>:/etc/pycsw/pycsw.cfg \
    -p 8000:8000 \
    geopython/pycsw


Supplying the configuration file via docker secrets:

docker secret create pycsw.cfg <path-to-pycsw.cfg>
docker service create --name pycsw --secret pycsw.cfg geopython/pycsw


sqlite repositories
+++++++++++++++++++

The default database repository is the CITE database that is used for running 
pycsw's test suites. Docker volumes may be used to specify custom sqlite 
database path. It should be mounted under ``/var/lib/pycsw``.

docker volume create pycsw-db-data
docker run --volume db-data:/var/lib/pycsw geopython/pycsw


postgresql repositories
+++++++++++++++++++++++

Specifying a postgresql repository is just a matter of configuring a custom
pycsw.cfg file with the correct specification.
Using a postgis database from the ``mdillon/postgis`` docker repository:


Logging
+++++++

In order to send logs to standard output, as is customary with docker 
containers, the pycsw.cfg file should specify the following:

``core.logfile=-``


Using pycsw in a standalone docker container
--------------------------------------------


docker run \
    --name pycsw \
    --dettach \
    --mount <path/to/pycsw/config>:/etc/pycsw/pycsw.cfg \
    --publish 8000:8000 \
    geopython/pycsw

sqlite


Using pycsw with docker compose
-------------------------------

Using pycsw with docker swarm
-----------------------------
