pycsw.org
=========

This is the setup for http://pycsw.org

Setting up website environment locally
--------------------------------------

    # setup virtualenv
    virtualenv pycsw-website && cd $_
    . bin/activate
    # get the website branch
    git clone git@github.com/geopython/pycsw.git -b website && cd pycsw
    # set Ruby environment variables
    . setenv-ruby
    # install Jekyll
    gem install jekyll

Workflow
--------

    # edit content
    jekyll build
    jekyll serve  # default port is 4000, set explicitly with -P 
    # view at http://localhost:4000
    # publish to live
    scp -r _site/* username@pycsw.org:/osgeo/pycsw-web
