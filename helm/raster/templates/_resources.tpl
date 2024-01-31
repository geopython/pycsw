{{/*
Create service name as used by the service name label.
*/}}
{{- define "service.fullname" -}}
{{- printf "%s-%s-%s" .Release.Name .Chart.Name "service" }}
{{- end }}

{{/*
Create configmap name as used by the service name label.
*/}}
{{- define "configmap.fullname" -}}
{{- printf "%s-%s-%s" .Release.Name .Chart.Name "configmap" | indent 1 }}
{{- end }}

{{/*
Create pycsw nginx configmap name as used by the service name label.
*/}}
{{- define "nginx-configmap.fullname" -}}
{{- printf "%s-%s-%s" .Release.Name .Chart.Name "nginx-configmap" | indent 1 }}
{{- end }}

{{/*
Create deployment name as used by the service name label.
*/}}
{{- define "deployment.fullname" -}}
{{- printf "%s-%s-%s" .Release.Name .Chart.Name "deployment" | indent 1 }}
{{- end }}

{{/*
Create mapproxy envoy configmap name as used by the service name label.
*/}}
{{- define "envoy-configmap.fullname" -}}
{{- printf "%s-%s-%s" .Release.Name .Chart.Name "envoy-configmap" | indent 1 }}
{{- end }}

{{/*
Create route name as used by the service name label.
*/}}
{{- define "route.fullname" -}}
{{- printf "%s-%s-%s" .Release.Name .Chart.Name "route" | indent 1 }}
{{- end }}

{{/*
Create ingress name as used by the service name label.
*/}}
{{- define "ingress.fullname" -}}
{{- printf "%s-%s-%s" .Release.Name .Chart.Name "ingress" | indent 1 }}
{{- end }}
