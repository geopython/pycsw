.. _pubsub:

Publish-Subscribe integration (Pub/Sub)
=======================================

pycsw supports Publish-Subscribe (Pub/Sub) integration by implementing
the `OGC API Publish-Subscribe Workflow - Part 1: Core`_ (draft) specification.

Pub/Sub integration can be enabled by defining a broker that pycsw can use to
publish notifications on given topics using CloudEvents (as per the specification).

When enabled, core functionality of Pub/Sub includes:

- displaying the broker link in the OGC API - Records landing (using the ``rel=hub`` link relation)
- sending a notification message on metadata transactions (create, replace, update, delete)

The following message queuing protocols are supported:

MQTT
----

Example directive:

.. code-block:: yaml

   pubsub:
       broker:
           type: mqtt
           url: mqtt://localhost:1883

.. note::

   For MQTT endpoints requiring authentication, encode the ``url`` value as follows: ``mqtt://username:password@localhost:1883``


.. _`OGC API Publish-Subscribe Workflow - Part 1: Core`: https://docs.ogc.org/DRAFTS/25-030.html
