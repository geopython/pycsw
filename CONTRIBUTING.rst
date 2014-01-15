Contributing to pycsw
=====================

The pycsw project openly welcomes contributions (bug reports, bug fixes, code
enhancements/features, etc.).  This document will outline some guidelines on
contributing to pycsw.  As well, pycsw `community </community.html>`_ is a great place to
get an idea of how to connect and participate in pycsw community and development.

GitHub
------

Code, tests, documentation, wiki and issue tracking are all managed on GitHub.
Make sure you have a `GitHub account <https://github.com/signup/free>`_.

Code Overview
-------------

- the pycsw `wiki <https://github.com/geopython/pycsw/wiki/Code-Architecture>`_ documents an overview of the codebase

Documentation
-------------

- documentation is managed in ``docs/``, in reStructuredText format
- `Sphinx`_ is used to generate the documentation
- See the `reStructuredText Primer <http://sphinx-doc.org/rest.html>`_ on rST markup and syntax.

Bugs
----

pycsw’s `issue tracker <https://github.com/geopython/pycsw/issues>`_ is the place to report bugs or request enhancements. To submit a bug be sure to specify the pycsw version you are using, the appropriate component, a description of how to reproduce the bug, as well as what version of Python and platform. For convenience, you can run ``pycsw-admin.py -c get_sysprof`` and copy/paste the output into your issue.

Forking pycsw
-------------

Contributions are most easily managed via GitHub pull requests.  `Fork <https://github.com/geopython/pycsw/fork>`_
pycsw into your own GitHub repository to be able to commit your work and submit pull requests.

Development
-----------

GitHub Commit Guidelines
^^^^^^^^^^^^^^^^^^^^^^^^

- enhancements and bug fixes should be identified with a GitHub issue
- commits should be granular enough for other developers to understand the nature / implications of the change(s)
- for trivial commits that do not need `Travis CI <https://travis-ci.org/geopython/pycsw>`_ to run, include ``[ci skip]`` as part of the commit message
- non-trivial Git commits shall be associated with a GitHub issue.  As documentation can always be improved, tickets need not be opened for improving the docs
- Git commits shall include a description of changes
- Git commits shall include the GitHub issue number (i.e. ``#1234``) in the Git commit log message
- all enhancements or bug fixes must successfully pass all :ref:`ogc-cite` tests before they are committed
- all enhancements or bug fixes must successfully pass all :ref:`tests` tests before they are committed
- enhancements which can be demonstrated from the pycsw :ref:`tests` should be accompanied by example CSW request XML

Coding Guidelines
^^^^^^^^^^^^^^^^^

- pycsw instead of PyCSW, pyCSW, Pycsw
- always code with `PEP 8`_ conventions
- always run source code through ``pep8`` and `pylint`_, using all pylint defaults except for ``C0111``.  ``sbin/pycsw-pylint.sh`` is included for convenience
- for exceptions which make their way to OGC ``ExceptionReport`` XML, always specify the appropriate ``locator`` and ``code`` parameters
- the pycsw wiki documents `developer tasks`_ for things like releasing documentation, testing, etc.

Submitting a Pull Request
^^^^^^^^^^^^^^^^^^^^^^^^^

This section will guide you through steps of working on pycsw.  This section assumes you have forked pycsw into your own GitHub repository.

.. code-block:: bash

  # setup a virtualenv
  $ virtualenv mypycsw && cd mypycsw
  $ . ./bin/activate
  # clone the repository locally
  $ git clone git@github.com:USERNAME/pycsw.git
  $ cd pycsw
  $ pip install -e . && pip install -r requirements.txt
  # add the main pycsw master branch to keep up to date with upstream changes
  $ git remote add upstream https://github.com/geopython/pycsw.git
  $ git pull upstream master
  # create a local branch off master
  # The name of the branch should include the issue number if it exists
  $ git branch 72-foo
  $ git checkout 72-foo
  # 
  # make code/doc changes
  #
  $ git commit -am 'fix xyz (#72-foo)'
  $ git push origin 72-foo

Your changes are now visible on your pycsw repository on GitHub.  You are now ready to create a pull request.
A member of the pycsw team will review the pull request and provide feedback / suggestions if required.  If changes are
required, make them against the same branch and push as per above (all changes to the branch in the pull request apply).

The pull request will then be merged by the pycsw team.  You can then delete your local branch (on GitHub), and then update
your own repository to ensure your pycsw repository is up to date with pycsw master:

.. code-block:: bash

  $ git checkout master
  $ git pull upstream master

GitHub Commit Access
--------------------

- proposals to provide developers with GitHub commit access shall be emailed to the pycsw-devel `mailing list </community.html#mailing_list>`_.  Proposals shall be approved by the pycsw development team.  Committers shall be added by the project admin
- removal of commit access shall be handled in the same manner
- each committer shall be listed in https://github.com/geopython/pycsw/blob/master/COMMITTERS.txt

.. _`PEP 8`: http://www.python.org/dev/peps/pep-0008/
.. _`pep8`: http://pypi.python.org/pypi/pep8/
.. _`pylint`: http://www.logilab.org/857
.. _`Sphinx`: http://sphinx-doc.org/
.. _`developer tasks`: https://github.com/geopython/pycsw/wiki/Developer-Tasks