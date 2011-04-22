.. _download:

Download
========

* `Current Release <https://sourceforge.net/projects/pycsw/files/0.1.0/>`_

* `All Releases <http://sourceforge.net/projects/pycsw/files/>`_

Source Code
------------------

* `SVN repository <https://pycsw.svn.sourceforge.net/svnroot/pycsw/trunk>`_

Packages
--------

OpenSUSE
********

pycsw exists as a `package <https://build.opensuse.org/package/show?package=pycsw&project=Application%3AGeo>`_ in openSUSE Build Service (OBS). Since release 0.1.0 it is included in the official 'Application:Geo <https://build.opensuse.org/project/show?project=Application%3AGeo>'_ repository. 

In order to install the OBS package in openSUSE 11.4, one can run the following commands as root:

.. code-block:: bash
  $zypper -ar http://download.opensuse.org/repositories/Application:/Geo/openSUSE_11.4/ GEO
  $zypper -ar http://download.opensuse.org/repositories/devel:/languages:/python/openSUSE_11.4/ python
  $zypper refresh
  $zypper install pycsw

For earlier openSUSE versions change "11.4" with "11.2" or "11.3". For future openSUSE version use "Factory".

An alternative method is to use the "One-Click Installer" from 'this <http://software.opensuse.org/search?q=pycsw&baseproject=openSUSE%3A11.4&lang=en&include_home=true&exclude_debug=true>'_ link.


