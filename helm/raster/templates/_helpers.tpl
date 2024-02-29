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
Returns the tag of the chart.
*/}}
{{- define "pycsw.tag" -}}
{{- default (printf "v%s" .Chart.AppVersion) .Values.image.tag }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "pycsw.selectorLabels" -}}
app.kubernetes.io/name: {{ include "pycsw.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Returns the environment from global if exists or from the chart's values, defaults to development
*/}}
{{- define "pycsw.environment" -}}
{{- if .Values.global.environment }}
    {{- .Values.global.environment -}}
{{- else -}}
    {{- .Values.environment | default "development" -}}
{{- end -}}
{{- end -}}

{{/*
Returns the pycsw server url based on the provided values, default localhost
*/}}
{{- define "pycsw.serverURL" -}}
    {{- if not .Values.route.host }}
        {{- printf "http://localhost:8000" -}}
    {{- else -}}
        {{- $protocol := .Values.route.https | ternary "httos" "http" -}}
        {{- printf "%s://%s" $protocol .Values.route.host -}}
        {{- if .Values.route.path -}}
            {{- printf "%s" .Values.route.path -}}
        {{- end -}}
    {{- end -}}
{{- end -}}

{{/*
Returns the cloud provider name from global if exists or from the chart's values, defaults to minikube
*/}}
{{- define "pycsw.cloudProviderFlavor" -}}
{{- if .Values.global.cloudProvider.flavor }}
    {{- .Values.global.cloudProvider.flavor -}}
{{- else if .Values.cloudProvider -}}
    {{- .Values.cloudProvider.flavor | default "minikube" -}}
{{- else -}}
    {{ "minikube" }}
{{- end -}}
{{- end -}}

{{/*
Returns the cloud provider docker registry url from global if exists or from the chart's values
*/}}
{{- define "pycsw.cloudProviderDockerRegistryUrl" -}}
{{- if .Values.global.cloudProvider.dockerRegistryUrl }}
    {{- printf "%s/" .Values.global.cloudProvider.dockerRegistryUrl -}}
{{- else if .Values.cloudProvider.dockerRegistryUrl -}}
    {{- printf "%s/" .Values.cloudProvider.dockerRegistryUrl -}}
{{- else -}}
{{- end -}}
{{- end -}}

{{/*
Returns the cloud provider image pull secret name from global if exists or from the chart's values
*/}}
{{- define "pycsw.cloudProviderImagePullSecretName" -}}
{{- if .Values.global.cloudProvider.imagePullSecretName }}
    {{- .Values.global.cloudProvider.imagePullSecretName -}}
{{- else if .Values.cloudProvider.imagePullSecretName -}}
    {{- .Values.cloudProvider.imagePullSecretName -}}
{{- end -}}
{{- end -}}

{{/*
Returns the tracing url from global if exists or from the chart's values
*/}}
{{- define "pycsw.tracingUrl" -}}
{{- if .Values.global.tracing.url }}
    {{- .Values.global.tracing.url -}}
{{- else if .Values.cloudProvider -}}
    {{- .Values.env.tracing.url -}}
{{- end -}}
{{- end -}}

{{/*
Returns the tracing url from global if exists or from the chart's values
*/}}
{{- define "pycsw.metricsUrl" -}}
{{- if .Values.global.metrics.url }}
    {{- .Values.global.metrics.url -}}
{{- else -}}
    {{- .Values.env.metrics.url -}}
{{- end -}}
{{- end -}}

{{- define "pycsw-pg-connection-string" -}}
{{- $db := (include "common.db.merged" .) | fromYaml }}
{{- "postgresql://${DB_USER}" -}}
{{- if .Values.env.db.requirePassword -}}
{{- ":${DB_PASSWORD}" -}}
{{- end -}}
{{- "@${DB_HOST}:${DB_PORT}/${DB_NAME}" -}}
{{- if $db.sslEnabled -}}
{{- "?sslmode=require" -}}
{{- if $db.secrets.caFileKey -}}
{{- "&sslrootcert=" -}}/.postgresql/ca.pem
{{- end -}}
{{- if $db.secrets.certFileKey -}}
{{- "&sslcert=" -}}/.postgresql/cert.pem
{{- end -}}
{{- if $db.secrets.keyFileKey -}}
{{- "&sslkey=" -}}/.postgresql/key.pem
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "pycsw.cors.allowedHeaders" -}}
{{- $authentication := (include "common.authentication.merged" .) | fromYaml }}
{{- $headerList := list -}}
{{- if ne .Values.env.cors.allowedHeaders "" -}}
{{- range $k, $v := (split "," .Values.env.cors.allowedHeaders) -}}
{{- $headerList = append $headerList $v -}}
{{- end -}}
{{- if ne $authentication.opa.customHeaderName "" -}}
{{- $headerList = append $headerList $authentication.opa.customHeaderName -}}
{{- end -}}
{{- $headerList = uniq $headerList -}}
{{-  quote (join "," $headerList) -}}
{{- else -}}
{{- $authentication.opa.customHeaderName | quote -}}
{{- end -}}
{{- end -}}
