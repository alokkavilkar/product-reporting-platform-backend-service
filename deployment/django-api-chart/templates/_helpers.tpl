{{/*
Return the full name of the chart with region suffix
*/}}
{{- define "django-api-chart.fullname" -}}
{{- if .Values.metadata.name -}}
{{- printf "%s-%s" .Values.metadata.name (default "us-east-1" .Values.metadata.region) | trunc 63 -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 -}}
{{- end -}}
{{- end }}

{{/*
Common selector labels for matching pods
*/}}
{{- define "django-api-chart.selectorLabels" -}}
app.kubernetes.io/name: {{ include "django-api-chart.fullname" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Standardized labels for all resources (recommended for prod)
*/}}
{{- define "django-api-chart.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
app.kubernetes.io/name: {{ include "django-api-chart.fullname" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/component: backend
app.kubernetes.io/part-of: product-report-platform
app.kubernetes.io/environment: {{ .Values.metadata.environment | default "production" }}
{{- end }}
