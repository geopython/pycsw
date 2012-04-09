#
# spec file for package pycsw (1.3-dev)
#
# Copyright (c) 2011 Angelos Tzotsos <tzotsos@opensuse.org>
#
# This file and all modifications and additions to the pycsw
# package are under the same license as the package itself.

%define _webappconfdir /etc/apache2/conf.d/
%define _htdocsdir /srv/www/htdocs/

%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}

Name:           pycsw
Version:        1.3-dev
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

cd ..
mv pycsw-1.3-dev %{buildroot}/srv/www/htdocs/pycsw
mkdir pycsw-1.3-dev

cat > %{buildroot}%{_sysconfdir}/apache2/conf.d/pycsw.conf << EOF
<Location /pycsw/>
  Options FollowSymLinks +ExecCGI
  Allow from all
  AddHandler cgi-script .py
</Location>
EOF

cat > %{buildroot}/srv/www/htdocs/pycsw/default.cfg << EOF
[server]
home=/srv/www/htdocs/pycsw
url=http://localhost/pycsw/csw.py
mimetype=application/xml; charset=UTF-8                                                             
encoding=UTF-8                                                                                      
language=en-US                                                                                      
maxrecords=10                                                                                       
#loglevel=DEBUG                                                                                     
#logfile=/tmp/pycsw.log
#ogc_schemas_base=http://foo
#federatedcatalogues=http://geodiscover.cgdi.ca/wes/serviceManagerCSW/csw
pretty_print=true
#gzip_compresslevel=8
profiles=apiso,fgdc,dif,ebrim

[manager]
transactions=false
allowed_ips=127.0.0.1

[metadata:main]
identification_title=pycsw Geospatial Catalogue
identification_abstract=pycsw is an OGC CSW server implementation written in Python
identification_keywords=catalogue,discovery
identification_keywords_type=theme
identification_fees=None
identification_accessconstraints=None
provider_name=pycsw
provider_url=http://pycsw.org/
contact_name=Kralidis, Tom
contact_position=Senior Systems Scientist
contact_address=TBA
contact_city=Toronto
contact_stateorprovince=Ontario
contact_postalcode=M9C 3Z9
contact_country=Canada
contact_phone=+01-416-xxx-xxxx
contact_fax=+01-416-xxx-xxxx
contact_email=tomkralidis@hotmail.com
contact_url=http://kralidis.ca/
contact_hours=0800h - 1600h EST
contact_instructions=During hours of service.  Off on weekends.
contact_role=pointOfContact

[repository]
# sqlite
database=sqlite:////srv/www/htdocs/pycsw/data/cite/records.db
# postgres
#database=postgresql://username:password@localhost/pycsw

[metadata:inspire]
enabled=true
languages_supported=eng,gre
default_language=eng
date=2011-03-29
gemet_keywords=Utility and governmental services
conformity_service=notEvaluated
contact_name=National Technical University of Athens
contact_email=tzotsos@gmail.com
temp_extent=2011-02-01/2011-03-30
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
