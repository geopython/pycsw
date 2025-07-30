{{/*
Expand the name of the chart.
*/}}
{{- define "pycsw.name" -}}
{{- default .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "pycsw.fullname" -}}
{{- $name := default .Chart.Name }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "pycsw.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "pycsw.labels" -}}
helm.sh/chart: {{ include "pycsw.chart" . }}
{{ include "pycsw.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "pycsw.selectorLabels" -}}
app.kubernetes.io/name: {{ include "pycsw.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Returns the environment from the chart's values if exists or from global, defaults to development
*/}}
{{- define "pycsw.environment" -}}
{{- if .Values.environment }}
    {{- .Values.environment -}}
{{- else -}}
    {{- .Values.global.environment | default "development" -}}
{{- end -}}
{{- end -}}

{{/*
  Returns the pycsw server url based on the provided values.  
*/}}
{{- define "pycsw.serverURL" -}}
  {{- $serverURL := "" }}
  {{- if not .Values.nginx.route.host }}
    {{- $serverURL = printf "http://localhost:8000" }}
  {{- else -}}
    {{- $protocol := .Values.nginx.route.tls.enabled | ternary "https" "http" }}
    {{- $serverURL = printf "%s://%s" $protocol .Values.nginx.route.host }}
    {{- if .Values.nginx.route.path }}
      {{- $serverURL = printf "%s%s" $serverURL .Values.nginx.route.path }}
    {{- end -}}
  {{- end -}}
  {{- printf "%s" $serverURL | quote }}
{{- end -}}

{{/*
Returns the cloud provider name from the chart's values if exists or from global, defaults to minikube
*/}}
{{- define "pycsw.cloudProviderFlavor" -}}
{{- if .Values.cloudProvider.flavor }}
    {{- .Values.cloudProvider.flavor -}}
{{- else -}}
    {{- .Values.global.cloudProvider.flavor | default "minikube" -}}
{{- end -}}
{{- end -}}

{{/*
Returns the tag of the chart.
*/}}
{{- define "pycsw.tag" -}}
{{- default (printf "v%s" .Chart.AppVersion) .Values.image.tag }}
{{- end }}

{{/*
Returns the cloud provider docker registry url from the chart's values if exists or from global
*/}}
{{- define "pycsw.cloudProviderDockerRegistryUrl" -}}
{{- if .Values.cloudProvider.dockerRegistryUrl }}
    {{- printf "%s/" .Values.cloudProvider.dockerRegistryUrl -}}
{{- else -}}
    {{- printf "%s/" .Values.global.cloudProvider.dockerRegistryUrl -}}
{{- end -}}
{{- end -}}

{{/*
Returns the cloud provider image pull secret name from the chart's values if exists or from global
*/}}
{{- define "pycsw.cloudProviderImagePullSecretName" -}}
{{- if .Values.cloudProvider.imagePullSecretName }}
    {{- .Values.cloudProvider.imagePullSecretName -}}
{{- else if .Values.global.cloudProvider.imagePullSecretName -}}
    {{- .Values.global.cloudProvider.imagePullSecretName -}}
{{- end -}}
{{- end -}}

{{- define "pycsw-pg-connection-string" -}}
{{- "postgresql://${DB_USER}" -}}
{{- if .Values.global.postgres.user.requirePassword -}}
{{- ":${DB_PASSWORD}" -}}
{{- end -}}
{{- "@${DB_HOST}:${DB_PORT}/${DB_NAME}" -}}
{{- if .Values.global.postgres.ssl.enabled -}}
{{- "?sslmode=require" -}}
{{- if .Values.global.postgres.ssl.caFileName -}}
{{- "&sslrootcert=" -}}/.postgresql/ca.pem
{{- end -}}
{{- if .Values.global.postgres.ssl.certFileName -}}
{{- "&sslcert=" -}}/.postgresql/cert.pem
{{- end -}}
{{- if .Values.global.postgres.ssl.keyFileName -}}
{{- "&sslkey=" -}}/.postgresql/key.pem
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "pycsw.cors.allowedHeaders" -}}
{{- $headerList := list -}}
{{- if ne .Values.authentication.cors.allowedHeaders "" -}}
{{- range $k, $v := (split "," .Values.authentication.cors.allowedHeaders) -}}
{{- $headerList = append $headerList $v -}}
{{- end -}}
{{- $headerList = uniq $headerList -}}
{{-  quote (join "," $headerList) -}}
{{- else -}}
""
{{- end -}}
{{- end -}}
