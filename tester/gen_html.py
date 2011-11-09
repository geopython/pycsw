#!/usr/bin/python
# =================================================================
#
# $Id$
#
# Authors: Tom Kralidis <tomkralidis@hotmail.com>
#
# Copyright (c) 2011 Tom Kralidis
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# =================================================================

import csv, os

jquery_version = '1.6.4'

print '''
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
    <head>
        <meta http-equiv="Content-Type" content="text/html;charset=utf-8"/>
        <meta http-equiv="Content-Style-Type" content="text/css"/>
        <meta http-equiv="pragma" content="no-cache"/>
        <meta http-equiv="Expires" content="Thu, 01 Dec 1994 120000 GMT"/>
        <title>pycsw Tester</title>
        <style type="text/css">
            body {
                background-color: #ffffff;
                font-family: arial, verdana, sans-serif;
                text-align: left;
                float: left;
            }
            .flat {
                border: 0px;
            }
        </style>
        <script type="text/javascript" src="http://code.jquery.com/jquery-%s.min.js"></script>
        <script type="text/javascript">
            $(document).ready(function() {
                $('.xml').change(function() {
                    if ($(this).val() != 'none') {
                        $.ajax({
                            type: 'GET',
                            url: $(this).val(),
                            dataType: 'text',
                            success: function(data) {
                                $('.request').val(data);
                            }
                        });
                    }
                });
                $('.send').click(function() {
                    $.ajax({
                        type: 'POST',
                        contentType: 'text/xml',
                        url: $('.server').val(),
                        data: $('.request').val(),
                        dataType: 'text',
                        success: function(data) {
                            $('.response').val(data);
                        },
                        error: function(data1) {
                            $('.response').val(data1.responseText);
                        }
                    });
                });
            });
        </script>
    </head>
''' % jquery_version

print '''
    <body>
        <h2 class="header">pycsw Tester</h2>
        <hr/>
        <h3 class="header">HTTP POST</h3>
        <form action="#" id="tester">
            <table>
                <tr>
                    <th>Request</th>
                    <th>Response</th>
                </tr>
                <tr>
                    <td>
                        <select class="xml">
                            <option value="none">Select a CSW Request</option>'''

for root, dirs, files in os.walk('suites'):
    if files:
        for file in files:
            if os.path.splitext(file)[1] in ['.xml']:  # it's a POST request
                query = '%s%s%s' % (root.replace(os.sep, '/'), '/', file)
                print '                            <option value="%s">%s</option>' % (query, query)
print '''
                        </select>
                        <input type="button" class="send" value="Send"/>
                    </td>
                    <td>
                        Server: <input type="text" size="40" class="server" value="../csw.py"/>
                    </td>
                </tr>
                <tr>
                    <td>
                        <textarea rows="20" cols="70" class="request"></textarea>
                    </td>
                    <td>
                        <textarea rows="20" cols="70" class="response"></textarea>
                    </td>
                </tr>
            </table>
        </form>
        <hr/>
        <h3 class="header">HTTP GET</h3>
            <ul>
'''
for root, dirs, files in os.walk('suites'):
    if files:
        for file in files:
            if file == 'requests.txt':  # it's a list of GET requests
                gets = csv.reader(open('%s%s%s' % (root.replace(os.sep, '/'), '/', file)))
                for row in gets:
                    query = row[1].replace('PYCSW_SERVER', '../csw.py')
                    print '<li><a href="%s">%s</a></li>' % (query, row[0])
print '''
            </ul>
        <hr/>
        <p>
            <a href="http://validator.w3.org/check?verbose=1&amp;uri=referer" title="[ Valid XHTML 1.0! ]"><img class="flat" src="http://www.w3.org/Icons/valid-xhtml10-blue" alt="[ Valid XHTML 1.0! ]" height="31" width="88"/></a>
            <a href="http://jigsaw.w3.org/css-validator/check/referer" title="[ Valid CSS! ]"><img class="flat" src="http://jigsaw.w3.org/css-validator/images/vcss-blue" alt="[ Valid CSS! ]" height="31" width="88"/></a>
        </p>
    </body>
</html>
'''
