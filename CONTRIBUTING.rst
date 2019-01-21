Contributing to pycsw
=====================

The pycsw project openly welcomes contributions (bug reports, bug fixes, code
enhancements/features, etc.).  This document will outline some guidelines on
contributing to pycsw.  As well, the pycsw `community <https://pycsw.org/community/>`_ is a great place to
get an idea of how to connect and participate in pycsw community and development.

pycsw has the following modes of contribution:

- GitHub Commit Access
- GitHub Pull Requests

Code of Conduct
---------------

Contributors to this project are expected to act respectfully toward others in accordance with the `OSGeo Code of Conduct <http://www.osgeo.org/code_of_conduct>`_.

Contributions and Licensing
---------------------------

Contributors are asked to confirm that they comply with project `license <https://github.com/geopython/pycsw/blob/master/LICENSE.txt>`_ guidelines.

GitHub Commit Access
^^^^^^^^^^^^^^^^^^^^

- proposals to provide developers with GitHub commit access shall be emailed to the pycsw-devel `mailing list`_.  Proposals shall be approved by the pycsw development team.  Committers shall be added by the project admin
- removal of commit access shall be handled in the same manner
- each committer must send an email to the pycsw mailing list agreeing to the license guidelines (see `Contributions and Licensing Agreement Template <#contributions-and-licensing-agreement-template>`_).  **This is only required once**
- each committer shall be listed in https://github.com/geopython/pycsw/blob/master/COMMITTERS.txt

GitHub Pull Requests
^^^^^^^^^^^^^^^^^^^^

- pull requests can provide agreement to license guidelines as text in the pull request or via email to the pycsw `mailing list`_  (see `Contributions and Licensing Agreement Template <#contributions-and-licensing-agreement-template>`_).  **This is only required for a contributor's first pull request.  Subsequent pull requests do not require this step**
- pull requests may include copyright in the source code header by the contributor if the contribution is significant or the contributor wants to claim copyright on their contribution
- all contributors shall be listed at https://github.com/geopython/pycsw/graphs/contributors
- unclaimed copyright, by default, is assigned to the main copyright holders as specified in https://github.com/geopython/pycsw/blob/master/LICENSE.txt

Contributions and Licensing Agreement Template
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``Hi all, I'd like to contribute <feature X|bugfix Y|docs|something else> to pycsw.
I confirm that my contributions to pycsw will be compatible with the pycsw
license guidelines at the time of contribution.``


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

pycsw's `issue tracker <https://github.com/geopython/pycsw/issues>`_ is the place to report bugs or request enhancements. To submit a bug be sure to specify the pycsw version you are using, the appropriate component, a description of how to reproduce the bug, as well as what version of Python and platform. For convenience, you can run ``pycsw-admin.py -c get_sysprof`` and copy/paste the output into your issue.

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
  virtualenv mypycsw && cd mypycsw
  . ./bin/activate
  # clone the repository locally
  git clone git@github.com:USERNAME/pycsw.git
  cd pycsw
  pip install -e . && pip install -r requirements-standalone.txt
  # add the main pycsw master branch to keep up to date with upstream changes
  git remote add upstream https://github.com/geopython/pycsw.git
  git pull upstream master
  # create a local branch off master
  # The name of the branch should include the issue number if it exists
  git branch issue-72
  git checkout issue-72
  # 
  # make code/doc changes
  #
  git commit -am 'fix xyz (#72)'
  git push origin issue-72

Your changes are now visible on your pycsw repository on GitHub.  You are now ready to create a pull request.
A member of the pycsw team will review the pull request and provide feedback / suggestions if required.  If changes are
required, make them against the same branch and push as per above (all changes to the branch in the pull request apply).

The pull request will then be merged by the pycsw team.  You can then delete your local branch (on GitHub), and then update
your own repository to ensure your pycsw repository is up to date with pycsw master:

.. code-block:: bash

  git checkout master
  git pull upstream master

.. _`Corporate`: http://www.osgeo.org/sites/osgeo.org/files/Page/corporate_contributor.txt
.. _`Individual`: http://www.osgeo.org/sites/osgeo.org/files/Page/individual_contributor.txt
.. _`info@osgeo.org`: mailto:info@osgeo.org
.. _`OSGeo`: http://www.osgeo.org/content/foundation/legal/licenses.html
.. _`PEP 8`: http://www.python.org/dev/peps/pep-0008/
.. _`pep8`: http://pypi.python.org/pypi/pep8/
.. _`pylint`: http://www.logilab.org/857
.. _`Sphinx`: http://sphinx-doc.org/
.. _`developer tasks`: https://github.com/geopython/pycsw/wiki/Developer-Tasks
.. _`mailing list`: https://pycsw.org/community#mailing-list
