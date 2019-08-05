#!/usr/bin/python
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2015 Tom Kralidis
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

import os

JQUERY_VERSION = '1.9.0'

print('''
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="utf-8"/>
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
                        var arr = $(this).val().split(',');
                        $.ajax({
                            type: 'GET',
                            url: arr[1],
                            dataType: 'text',
                            success: function(data) {
                                $('.request').val(data);
                                $('.server').val('../csw.py?config=' + arr[0]);
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
''' % JQUERY_VERSION)

print('''
    <body>
        <h2 class="header">pycsw Tester</h2>
        <hr/>
        <h3 class="header">HTTP POST</h3>
        <form action="#" id="tests">
            <table>
                <tr>
                    <th>Request</th>
                    <th>Response</th>
                </tr>
                <tr>
                    <td>
                        <select class="xml">
                            <option value="none">Select a CSW Request</option>''')

for root, dirs, files in os.walk('functionaltests/suites'):
    if files:
        for sfile in files:
            if os.path.splitext(sfile)[1] in ['.xml'] and 'post' in root:  # it's a POST request
                query = '%s%s%s' % (root.replace(os.sep, '/'), '/', sfile)
                print('                            <option value="tests/functionaltests/suites/%s/default.cfg,%s">%s</option>' % (root.split(os.sep)[2], query, query))
print('''
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
''')

for root, dirs, files in os.walk('functionaltests/suites'):
    if files:
        for sfile in files:
            if sfile == 'requests.txt':  # it's a list of GET requests
                file_path = os.path.join(root, sfile)
                with open(file_path) as f:
                    for line in f:
                        name, query_string = line.strip().partition(",")[::2]
                        baseurl = "../csw.py"
                        query = "{baseurl}?{query_string}".format(
                            baseurl=baseurl,
                            query_string=query_string.replace("&", "&amp;")
                        )
                        print('<li><a href={query!r}>{name}</a></li>'.format(
                            query=query, name=name))
print('''
            </ul>
        <hr/>
        <footer>
            <a href="http://validator.w3.org/check?verbose=1&amp;uri=referer" title="Valid HTML 5!"><img class="flat" src="http://www.w3.org/html/logo/downloads/HTML5_Badge_32.png" alt="Valid HTML 5!" height="32" width="32"/></a>
            <a href="http://jigsaw.w3.org/css-validator/check/referer" title="Valid CSS!"><img class="flat" src="http://jigsaw.w3.org/css-validator/images/vcss-blue" alt="Valid CSS!" height="31" width="88"/></a>
        </footer>
    </body>
</html>
''')
