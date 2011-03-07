.. _tester:

.. raw:: html

   <script type="text/javascript">
     $(document).ready(function() {
       $('.xml').change(function() {
         if ($(this).val() != 'none') {
           $.ajax({
             type: 'GET',
             url: '_static/tester/'+$(this).val(),
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

============
pycsw Tester
============

.. raw:: html

   <h3>Request</h3>
   <form id="tester">
     <select class="xml">
       <option value="none">Select a CSW Request</option> 
       <optgroup label="GetCapabilities">
         <option value="GetCapabilities.xml">GetCapabilities</option> 
         <option value="GetCapabilities-SOAP.xml">GetCapabilities-SOAP</option> 
       </optgroup>
       <optgroup label="DescribeRecord">
         <option value="DescribeRecord.xml">DescribeRecord</option> 
       </optgroup>
       <optgroup label="GetDomain">
         <option value="GetDomain-property.xml">GetDomain-property</option> 
         <option value="GetDomain-parameter.xml">GetDomain-parameter</option> 
       </optgroup>
       <optgroup label="GetRecords">
         <option value="GetRecords-all.xml">GetRecords-all</option> 
         <option value="GetRecords-filter-anytext.xml">GetRecords-filter-anytext</option> 
         <option value="GetRecords-filter-bbox.xml">GetRecords-filter-bbox</option> 
         <option value="GetRecords-filter-not-bbox.xml">GetRecords-filter-not-bbox</option> 
         <option value="GetRecords-filter-and-bbox-freetext.xml">GetRecords-filter-and-bbox-freetext.xml</option> 
         <option value="GetRecords-filter-or-bbox-freetext.xml">GetRecords-filter-or-bbox-freetext.xml</option> 
         <option value="GetRecords-filter-or-title-abstract.xml">GetRecords-filter-or-title-abstract.xml</option> 
         <option value="GetRecords-cql-title.xml">GetRecords-cql-title</option> 
       </optgroup>
       <optgroup label="GetRecordById">
         <option value="GetRecordById.xml">GetRecordById</option> 
       </optgroup>
       <optgroup label="Transaction">
       </optgroup>
       <optgroup label="Harvest">
       </optgroup>
     </select>
     <br/><br/>
     <textarea rows="15" cols="70" class="request"></textarea>
     <h3>Server <input type="text" size="40" class="server" value="http://host/pycsw/csw.py"/> <input type="button" class="send" value="Send"/></h3>
     <h3>Response</h3>
     <textarea rows="15" cols="70" class="response"></textarea>
   </form>
