{{/*
Expand the name of the chart.
*/}}
{{- define "multi-agent-system.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "multi-agent-system.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "multi-agent-system.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "multi-agent-system.labels" -}}
helm.sh/chart: {{ include "multi-agent-system.chart" . }}
{{ include "multi-agent-system.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
environment: {{ .Values.global.environment }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "multi-agent-system.selectorLabels" -}}
app.kubernetes.io/name: {{ include "multi-agent-system.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Router Agent labels
*/}}
{{- define "router-agent.labels" -}}
{{ include "multi-agent-system.labels" . }}
app: {{ .Values.routerAgent.name }}
tier: orchestrator
{{- end }}

{{/*
SDB Agent labels
*/}}
{{- define "sdb-agent.labels" -}}
{{ include "multi-agent-system.labels" . }}
app: {{ .Values.sdbAgent.name }}
tier: worker
{{- end }}

{{/*
Image name helper
*/}}
{{- define "image.name" -}}
{{- if eq .registry "docker.io" }}
{{- printf "%s:%s" .repository .tag }}
{{- else }}
{{- printf "%s/%s:%s" .registry .repository .tag }}
{{- end }}
{{- end }}

