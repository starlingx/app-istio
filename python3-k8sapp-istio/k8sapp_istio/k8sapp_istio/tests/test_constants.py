#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Unit tests for constants module."""

import unittest

from k8sapp_istio.common import constants as app_constants


class TestConstants(unittest.TestCase):
    """Test all constant values in the module."""

    def test_helm_app_istio(self):
        """Test HELM_APP_ISTIO constant value."""
        self.assertEqual(
            app_constants.HELM_APP_ISTIO, 'istio')

    def test_helm_ns_istio_system(self):
        """Test HELM_NS_ISTIO_SYSTEM constant."""
        self.assertEqual(
            app_constants.HELM_NS_ISTIO_SYSTEM,
            'istio-system')

    def test_helm_chart_istio_base(self):
        """Test HELM_CHART_ISTIO_BASE constant."""
        self.assertEqual(
            app_constants.HELM_CHART_ISTIO_BASE, 'base')

    def test_helm_chart_istio_cni(self):
        """Test HELM_CHART_ISTIO_CNI constant."""
        self.assertEqual(
            app_constants.HELM_CHART_ISTIO_CNI, 'cni')

    def test_helm_chart_istio_pilot(self):
        """Test HELM_CHART_ISTIO_PILOT constant."""
        self.assertEqual(
            app_constants.HELM_CHART_ISTIO_PILOT,
            'istiod')

    def test_helm_chart_istio_gateways(self):
        """Test HELM_CHART_ISTIO_GATEWAYS constant."""
        self.assertEqual(
            app_constants.HELM_CHART_ISTIO_GATEWAYS,
            'gateways')

    def test_helm_chart_istio_ingressgateway(self):
        """Test HELM_CHART_ISTIO_INGRESSGATEWAY."""
        self.assertEqual(
            app_constants.HELM_CHART_ISTIO_INGRESSGATEWAY,
            'istio-ingress')

    def test_helm_chart_istio_egressgateway(self):
        """Test HELM_CHART_ISTIO_EGRESSGATEWAY."""
        self.assertEqual(
            app_constants.HELM_CHART_ISTIO_EGRESSGATEWAY,
            'istio-egress')

    def test_helm_chart_kiali_server(self):
        """Test HELM_CHART_KIALI_SERVER constant."""
        self.assertEqual(
            app_constants.HELM_CHART_KIALI_SERVER,
            'kiali-server')

    def test_helm_component_label_istio(self):
        """Test HELM_COMPONENT_LABEL_ISTIO."""
        self.assertEqual(
            app_constants.HELM_COMPONENT_LABEL_ISTIO,
            'app.starlingx.io/component')

    def test_constants_are_strings(self):
        """Test all constants are string type."""
        constant_names = [
            'HELM_APP_ISTIO',
            'HELM_NS_ISTIO_SYSTEM',
            'HELM_CHART_ISTIO_BASE',
            'HELM_CHART_ISTIO_CNI',
            'HELM_CHART_ISTIO_PILOT',
            'HELM_CHART_ISTIO_GATEWAYS',
            'HELM_CHART_ISTIO_INGRESSGATEWAY',
            'HELM_CHART_ISTIO_EGRESSGATEWAY',
            'HELM_CHART_KIALI_SERVER',
            'HELM_COMPONENT_LABEL_ISTIO',
        ]
        for constant_name in constant_names:
            self.assertIsInstance(
                getattr(app_constants, constant_name),
                str,
                msg="{} is not a string".format(
                    constant_name))
