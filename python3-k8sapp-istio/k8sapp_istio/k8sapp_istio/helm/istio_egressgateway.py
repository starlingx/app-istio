#
# Copyright (c) 2025 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from sysinv.common import exception
from sysinv.helm import base

from k8sapp_istio.common import constants as app_constants


class IstioEgressGatewayHelm(base.FluxCDBaseHelm):
    """Class to encapsulate helm operations for the istio-egress chart"""

    SUPPORTED_NAMESPACES = base.BaseHelm.SUPPORTED_NAMESPACES + \
        [app_constants.HELM_NS_ISTIO_SYSTEM]
    SUPPORTED_APP_NAMESPACES = {
        app_constants.HELM_APP_ISTIO:
            base.BaseHelm.SUPPORTED_NAMESPACES +
            [app_constants.HELM_NS_ISTIO_SYSTEM]
    }

    CHART = app_constants.HELM_CHART_ISTIO_EGRESSGATEWAY

    SERVICE_NAME = app_constants.HELM_APP_ISTIO
    HELM_RELEASE = app_constants.HELM_CHART_ISTIO_EGRESSGATEWAY

    def _is_enabled(self, app_name, chart_name, namespace):
        """
        Check if the chart is enable at a system level

        :param app_name: Application name
        :param chart_name: Chart supplied with the application
        :param namespace: Namespace where the chart will be executed

        Returns true by default if an exception occurs as most charts are
        enabled.
        """
        return super(IstioEgressGatewayHelm, self)._is_enabled(
            app_name, chart_name, namespace)

    def execute_kustomize_updates(self, operator):
        """
        Update the elements of FluxCD kustomize manifests.

        This allows a helm chart plugin to use the FluxCDKustomizeOperator to
        make dynamic structural changes to the application manifest based on the
        current conditions in the platform

        Changes currenty include updates to the top level kustomize manifest to
        disable helm releases.

        :param operator: an instance of the FluxCDKustomizeOperator
        """
        if not self._is_enabled(operator.APP, self.CHART,
                                app_constants.HELM_NS_ISTIO_SYSTEM):
            operator.helm_release_resource_delete(self.HELM_RELEASE)

    def get_namespaces(self):
        return self.SUPPORTED_NAMESPACES

    def get_overrides(self, namespace=None):
        overrides = {
            app_constants.HELM_NS_ISTIO_SYSTEM: {}
        }

        if namespace in self.SUPPORTED_NAMESPACES:
            return overrides[namespace]
        elif namespace:
            raise exception.InvalidHelmNamespace(chart=self.CHART,
                                                 namespace=namespace)
        else:
            return overrides
