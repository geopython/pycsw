#
# spec file for package pycsw
#
# Copyright (c) 2011 Angelos Tzotsos <tzotsos@opensuse.org>
#
# This file and all modifications and additions to the pristine
# package are under the same license as the package itself.

%define _webappconfdir /etc/apache2/conf.d/
%define _htdocsdir /srv/www/htdocs/

%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}

Name:           pycsw
Version:        1.2.0
Release:        1
License:        MIT
Summary:        An OGC CSW server implementation written in Python
Url:            http://pycsw.org/
Group:          Development/Tools
Source0:        %{name}-%{version}.tar.gz
Requires:	python
Requires:	python-sqlalchemy
Requires:	python-Shapely
Requires:	python-lxml
Requires:	python-pyproj
Requires:	apache2
BuildRequires:  fdupes python 

BuildRoot:      %{_tmppath}/%{name}-%{version}-build

###%{py_requires}

###%lang_package

%description
pycsw implements clause 10 (HTTP protocol binding (Catalogue Services for the Web, CSW)) 
of the OpenGIS Catalogue Service Implementation Specification, version 2.0.2. 
Initial development started in 2010 (more formally announced in 2011).
pycsw allows for the publishing and discovery of geospatial metadata. Existing repositories of geospatial metadata can be exposed via OGC:CSW 2.0.2.
pycsw is Open Source, released under an MIT license, and runs on all major platforms (Windows, Linux, Mac OS X)


%prep
%setup -q

%build

%install
mkdir -p %{buildroot}/srv/www/htdocs
mkdir -p %{buildroot}%{_sysconfdir}/apache2/conf.d

mv pycsw %{buildroot}/srv/www/htdocs/

cat > %{buildroot}%{_sysconfdir}/apache2/conf.d/pycsw.conf << EOF
<Location /pycsw/>
  Options FollowSymLinks +ExecCGI
  Allow from all
  AddHandler cgi-script .py
</Location>
EOF

%fdupes -s %{buildroot}

%post 

%clean
rm -rf '%{buildroot}'

%files
%defattr(-,root,root)
%config(noreplace) %{_webappconfdir}/pycsw.conf
%dir %{_sysconfdir}/apache2/
%dir %{_webappconfdir}/
%dir %{_htdocsdir}/pycsw/
%{_htdocsdir}/pycsw/*

%changelog
