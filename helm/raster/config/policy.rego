package envoy.authz

import input.attributes.metadataContext.filterMetadata["envoy.filters.http.jwt_authn"].map_colonies_token_payload as payload
import input.attributes.metadataContext.filterMetadata.map_colonies as map_colonies
import input.attributes.request.http as http_request

default allow = false

user_has_resource_access[payload] {
	lower(payload.d[_]) = lower(map_colonies.domain)
}

valid_origin[payload] {
	payload.ao[_] = http_request.headers.origin
}

valid_origin[payload] {
	payload.ao == http_request.headers.origin
}

valid_referrer[payload] {
	payload.ao[_] = http_request.headers.referrer
}

valid_referrer[payload] {
	payload.ao == http_request.headers.referrer
}

valid_origin[payload] {
	not payload.ao
}eyJhbGciOiJSUzI1NiIsImtpZCI6Ik1hcENvbG9uaWVzUUEifQ.eyJkIjpbInJhc3RlciIsInJhc3RlcldtcyIsInJhc3RlckV4cG9ydCIsImRlbSIsInZlY3RvciIsIjNkIl0sImlhdCI6MTY2Mzg2MzM0Mywic3ViIjoiTWFwQ29sb25pZXNRQSIsImlzcyI6Im1hcGNvbG9uaWVzLXRva2VuLWNsaSIsImFvIjpbImh0dHA6Ly9ibGFibGEvIl19.SdgSAOrTFHJAh1fRIOCq1Mvn49xz3lv_R-gu0IECM7JXE4zhVnvBrERVNb7zZYbSHZ8pAakP79OFVsMT0j7_BWwZpjTMLzesEJ8nIqb_JD7NQZRpE7jzrfG70AZcSrFuREFjK2I9cLPibPhPXF90Nu4iNsoR7Y2hgo94LAcPW_NUDDSIB-cRr0js8iFjMkV_mcx16uvoxgvYWS2jXbaYeRn3M2qLQb9xv_ikp5hIVma00OMg3w7L-dPdXJ36fJPL8DSi8fKTG3d0PkqRbBD-Fz-4eczKJ7HeJgGF9wEzgpUfGTmK2qSOyEJel9h3meY0Tv7O2ZzLPxmFFFIYH_OlKA

# allow authenticated acess
allow {
	valid_origin[payload]
	user_has_resource_access[payload]
}

allow {
	valid_referrer[payload]
	user_has_resource_access[payload]
}

# allow cors preflight WITHOUT AUTHENTICATION
allow {
	http_request.method == "OPTIONS"
	_ = http_request.headers["access-control-request-method"]
	_ = http_request.headers["access-control-request-headers"]
}
