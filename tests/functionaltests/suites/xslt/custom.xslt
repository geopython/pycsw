<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:csw="http://www.opengis.net/cat/csw/2.0.2" xmlns:dc="http://purl.org/dc/elements/1.1/">
    <xsl:template match="csw:Record">
        <foo><xsl:value-of select="dc:title"/></foo>
    </xsl:template>
</xsl:stylesheet>
