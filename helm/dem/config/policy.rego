package envoy.authz

import input.attributes.request.http as http_request
import input.attributes.metadataContext.filterMetadata["envoy.filters.http.jwt_authn"].map_colonies_token_payload as payload
import input.attributes.metadataContext.filterMetadata.map_colonies as map_colonies

# Decline until I allow it.
default allow = false

### Resources Access ###
user_has_resource_access[payload] {
	lower(payload.d[_]) = lower(map_colonies.domain)
}
### Resources Access ###

### ORIGIN and REFERRER ###
# Checks if origin is in allowed origin
valid_origin[payload] {
	payload.ao[_] = http_request.headers.origin
}

# Checks if origin is allowed origin (if ao is not an arr)
valid_origin[payload] {
	payload.ao == http_request.headers.origin
}

# Checks if referrer is in allowed origin
valid_referrer[payload] {
  payload.ao[_] = http_request.headers.referrer
}

# Checks if referrer is allowed origin (if ao is not an arr)
valid_referrer[payload] {
  payload.ao == http_request.headers.referrer
}

# Checks if there is allowed origin
valid_origin[payload] {
	not payload.ao
}
### ORIGIN and REFERRER ###

# Allow authenticated access
allow {
  valid_origin[payload]
  user_has_resource_access[payload]
}

# For future use when referrer check is needed
#allow {
#  valid_referrer[payload]
#  user_has_resource_access[payload]
#}

# Allow cors preflight WITHOUT AUTHENTICATION
allow {
	http_request.method == "OPTIONS"
	_ = http_request.headers["access-control-request-method"]
	_ = http_request.headers["access-control-request-headers"]
}
