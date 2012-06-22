.. _development:

Development
===========

Code Overview
-------------

- the pycsw `wiki <https://github.com/geopython/pycsw/wiki/Code-Architecture>`_ documents an overview of the codebase

Subversion
----------

- pycsw source code and documentation are managed using Subversion.  lxml, Shapely, pyproj and sqlalchemy are required for pycsw to be functional
- documentation is managed in ``docs/``, in reStructuredText format.  `Sphinx`_ is used to generate the docs

Submitting Patches
------------------

- where possible, submit patches as part of a trac ticket (see :ref:`support`)

Subversion Commit Access
------------------------

- proposals to provide developers with SVN commit access shall be emailed to the pycsw-devel mailing list (see :ref:`mailing-lists`).  Proposals shall be approved by the pycsw development team.  Committers shall be added by the project admin
- removal of commit access shall be handled in the same manner
- each committer shall be listed in https://github.com/geopython/pycsw/blob/master/COMMITTERS.txt
 
Subversion Commit Guidelines
----------------------------

- enhancements and bug fixes shall be identified with a trac ticket
- non-trivial SVN commits shal be associated with a trac ticket.  As documentation can always be improved, tickets need not be opened for improving the docs
- SVN commits shall include a description of changes
- SVN commits shall include the trac ticket number (i.e. ``#1234``) in the SVN commit log message
- trac ticket updates shall include SVN changeset numbers (i.e. ``r1234``)
- all enhancements or bug fixes must successfully pass all :ref:`ogc-cite` tests before they are committed
- all enhancements or bug fixes must successfully pass all :ref:`tester` tests before they are committed
- enhancements which can be demonstrated from the pycsw :ref:`tester` should be accompanied by example CSW request XML

Coding and Documentation Guidelines
-----------------------------------

- pycsw instead of PyCSW, pyCSW, Pycsw
- always code with `PEP 8`_ conventions
- always run source code through `pylint`_, using all pylint defaults except for ``C0111``.  ``sbin/pycsw-pylint.sh`` is included for convenience
- for exceptions which make their way to OGC ``ExceptionReport`` XML, always specify the appropriate ``locator`` and ``code`` parameters

.. _`PEP 8`: http://www.python.org/dev/peps/pep-0008/
.. _`pylint`: http://www.logilab.org/857
.. _`Sphinx`: http://sphinx.pocoo.org/
