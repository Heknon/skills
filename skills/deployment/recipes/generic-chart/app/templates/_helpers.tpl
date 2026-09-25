{{/* Name of every object: fullnameOverride, or the release name. 53 characters leaves room for suffixes. */}}
{{- define "app.fullname" -}}
{{- default .Release.Name .Values.fullnameOverride | trunc 53 | trimSuffix "-" -}}
{{- end -}}

{{/* Labels that never change for a release. Used as the selector, so never add a value that changes per upgrade. */}}
{{- define "app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "app.fullname" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "app.labels" -}}
{{ include "app.selectorLabels" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" }}
{{- with .Values.image.tag }}
app.kubernetes.io/version: {{ . | quote }}
{{- end }}
{{- end -}}

{{/* repository@digest when a digest is given, else repository:tag. One of them is required. */}}
{{- define "app.image" -}}
{{- if .Values.image.digest -}}
{{ .Values.image.repository }}@{{ .Values.image.digest }}
{{- else -}}
{{ .Values.image.repository }}:{{ required "set image.tag or image.digest" .Values.image.tag }}
{{- end -}}
{{- end -}}

{{- define "app.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{ include "app.fullname" . }}
{{- else -}}
{{ default "default" .Values.serviceAccount.name }}
{{- end -}}
{{- end -}}

{{/* Security context that passes Pod Security "restricted" and OpenShift "restricted-v2".
     No runAsUser or fsGroup: OpenShift assigns them from the namespace's range. */}}
{{- define "app.podSecurityContext" -}}
runAsNonRoot: true
seccompProfile:
  type: RuntimeDefault
{{- end -}}

{{- define "app.containerSecurityContext" -}}
allowPrivilegeEscalation: false
readOnlyRootFilesystem: true
capabilities:
  drop: ["ALL"]
{{- end -}}

{{/* Environment shared by the main container, the migration Job and the CronJobs. */}}
{{- define "app.envBlock" -}}
{{- with .Values.env }}
env:
{{- range $name, $value := . }}
  - name: {{ $name }}
    value: {{ $value | quote }}
{{- end }}
{{- end }}
{{- with .Values.envFromSecrets }}
envFrom:
{{- range . }}
  - secretRef:
      name: {{ . }}
{{- end }}
{{- end }}
{{- end -}}

{{/* Volumes: a writable /tmp, since the root filesystem is read only, and the config files. */}}
{{- define "app.volumes" -}}
volumes:
  - name: tmp
    emptyDir: {}
{{- if .Values.config.files }}
  - name: config
    configMap:
      name: {{ include "app.fullname" . }}
{{- end }}
{{- end -}}

{{- define "app.volumeMounts" -}}
volumeMounts:
  - name: tmp
    mountPath: /tmp
{{- if .Values.config.files }}
  - name: config
    mountPath: {{ .Values.config.mountPath }}
    readOnly: true
{{- end }}
{{- end -}}

{{/* A container running the image with the shared env, for Jobs. Call with (dict "root" $ "command" ... "args" ...). */}}
{{- define "app.jobContainer" -}}
- name: job
  image: {{ include "app.image" .root }}
  imagePullPolicy: {{ .root.Values.image.pullPolicy }}
  {{- with .command }}
  command: {{ toJson . }}
  {{- end }}
  {{- with .args }}
  args: {{ toJson . }}
  {{- end }}
  {{- include "app.envBlock" .root | nindent 2 }}
  {{- include "app.volumeMounts" .root | nindent 2 }}
  securityContext:
    {{- include "app.containerSecurityContext" .root | nindent 4 }}
  resources:
    {{- toYaml .root.Values.resources | nindent 4 }}
{{- end -}}
