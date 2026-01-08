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
           channel: messages/a/data  # optional

HTTP
----

Example directive:

.. code-block:: yaml

   pubsub:
       broker:
           type: http
           url: https://ntfy.sh
           channel: messages-a-data  # optional

.. note::

   For any Pub/Sub endpoints requiring authentication, encode the ``url`` value as follows:

   * ``mqtt://username:password@localhost:1883``
   * ``https://username:password@localhost``

.. note::

   If no ``channel`` is defined, the relevant OGC API endpoint is used.

.. _`OGC API Publish-Subscribe Workflow - Part 1: Core`: https://docs.ogc.org/DRAFTS/25-030.html
