# 2015-02-13

The unofficial CSW 3.0 schema can be tested from here.

http://test.schemas.opengis.net/csw/3.0/

I did make one change to the examples/Capabilities.xml

Thanks,

kevin

####################################################################
--- csw3_0_0-beta-20150123-pv/csw/3.0/examples/Capabilities.xml
+++ csw3_0_0-beta-20150123-pv-s1/csw/3.0/examples/Capabilities.xml
@@ -15,7 +15,7 @@
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.opengis.net/cat/csw/3.0
-                       http://www.opengis.net/csw/3.0/cswAll.xsd
+                       http://schemas.opengis.net/csw/3.0/cswAll.xsd
                        http://www.opengis.net/gml/3.2
                        http://schemas.opengis.net/gml/3.2.1/gml.xsd
                        http://www.w3.org/1999/xlink

