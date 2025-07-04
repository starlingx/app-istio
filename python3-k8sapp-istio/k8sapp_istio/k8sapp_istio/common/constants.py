#
# Copyright (c) 2022-2025 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

# Application Name
HELM_APP_ISTIO = 'istio'

# Namespace to deploy the application
HELM_NS_ISTIO_SYSTEM = 'istio-system'

# Helm: Supported charts:
# These values match the names in the chart package's Chart.yaml

HELM_CHART_ISTIO_BASE = 'base'
HELM_CHART_ISTIO_CNI = 'cni'
HELM_CHART_ISTIO_PILOT = 'istiod'
HELM_CHART_ISTIO_GATEWAYS = 'gateways'
HELM_CHART_ISTIO_INGRESSGATEWAY = 'istio-ingress'
HELM_CHART_ISTIO_EGRESSGATEWAY = 'istio-egress'
HELM_CHART_KIALI_SERVER = 'kiali-server'

HELM_COMPONENT_LABEL_ISTIO = 'app.starlingx.io/component'
