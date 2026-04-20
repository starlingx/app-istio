#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Unit tests for helm chart classes."""

import unittest
from unittest import mock

from k8sapp_istio.common import constants as app_constants


class BaseHelmTestMixin(object):
    """Mixin providing common helm chart tests.

    Subclasses must set:
        HELM_CLASS_PATH - dotted import path
        HELM_CLASS_NAME - class name string
        EXPECTED_CHART - expected CHART value
        EXPECTED_HELM_RELEASE - expected release
    """

    HELM_CLASS_PATH = None
    HELM_CLASS_NAME = None
    EXPECTED_CHART = None
    EXPECTED_HELM_RELEASE = None

    def _make_instance(self):
        """Create helm class instance with mock.

        Returns an instance with mocked operator.
        """
        operator = mock.MagicMock()
        operator.dbapi = mock.MagicMock()
        with mock.patch(
            'sysinv.helm.base.BaseHelm.__init__',
            return_value=None
        ):
            helm_class = self._get_class()
            instance = helm_class.__new__(
                helm_class)
            instance._operator = operator
        return instance

    def _get_class(self):
        """Import and return the helm class."""
        raise NotImplementedError

    def test_chart_constant(self):
        """Test CHART attribute matches expected."""
        helm_class = self._get_class()
        self.assertEqual(
            helm_class.CHART,
            self.EXPECTED_CHART)

    def test_helm_release_constant(self):
        """Test HELM_RELEASE matches expected."""
        helm_class = self._get_class()
        self.assertEqual(
            helm_class.HELM_RELEASE,
            self.EXPECTED_HELM_RELEASE)

    def test_service_name(self):
        """Test SERVICE_NAME is set to istio."""
        helm_class = self._get_class()
        self.assertEqual(
            helm_class.SERVICE_NAME,
            app_constants.HELM_APP_ISTIO)

    def test_supported_namespaces_contains_istio(self):
        """Test SUPPORTED_NAMESPACES has istio."""
        helm_class = self._get_class()
        self.assertIn(
            app_constants.HELM_NS_ISTIO_SYSTEM,
            helm_class.SUPPORTED_NAMESPACES)

    def test_supported_app_namespaces(self):
        """Test SUPPORTED_APP_NAMESPACES has istio."""
        helm_class = self._get_class()
        self.assertIn(
            app_constants.HELM_APP_ISTIO,
            helm_class.SUPPORTED_APP_NAMESPACES)
        namespace_list = (
            helm_class.SUPPORTED_APP_NAMESPACES[
                app_constants.HELM_APP_ISTIO])
        self.assertIn(
            app_constants.HELM_NS_ISTIO_SYSTEM,
            namespace_list)

    def test_get_namespaces(self):
        """Test get_namespaces returns supported."""
        instance = self._make_instance()
        result = instance.get_namespaces()
        self.assertEqual(
            result,
            instance.SUPPORTED_NAMESPACES)

    def test_get_overrides_valid_namespace(self):
        """Test get_overrides with valid namespace."""
        instance = self._make_instance()
        result = instance.get_overrides(
            namespace=(
                app_constants.HELM_NS_ISTIO_SYSTEM))
        self.assertIsInstance(result, dict)

    def test_get_overrides_no_namespace(self):
        """Test get_overrides with no namespace."""
        instance = self._make_instance()
        result = instance.get_overrides(
            namespace=None)
        self.assertIsInstance(result, dict)
        self.assertIn(
            app_constants.HELM_NS_ISTIO_SYSTEM,
            result)

    def test_get_overrides_invalid_namespace(self):
        """Test get_overrides with invalid namespace."""
        instance = self._make_instance()
        from sysinv.common import exception
        self.assertRaises(
            exception.InvalidHelmNamespace,
            instance.get_overrides,
            namespace='invalid-ns')

    @mock.patch(
        'sysinv.common.utils.is_chart_enabled',
        return_value=True)
    def test_is_enabled_true(
        self, mock_chart_enabled
    ):
        """Test _is_enabled returns True."""
        instance = self._make_instance()
        result = instance._is_enabled(
            app_constants.HELM_APP_ISTIO,
            self.EXPECTED_CHART,
            app_constants.HELM_NS_ISTIO_SYSTEM)
        self.assertTrue(result)

    @mock.patch(
        'sysinv.common.utils.is_chart_enabled',
        return_value=False)
    def test_is_enabled_false(
        self, mock_chart_enabled
    ):
        """Test _is_enabled returns False."""
        instance = self._make_instance()
        result = instance._is_enabled(
            app_constants.HELM_APP_ISTIO,
            self.EXPECTED_CHART,
            app_constants.HELM_NS_ISTIO_SYSTEM)
        self.assertFalse(result)

    @mock.patch(
        'sysinv.common.utils.is_chart_enabled',
        return_value=False)
    def test_kustomize_updates_disabled(
        self, mock_chart_enabled
    ):
        """Test kustomize deletes when disabled."""
        instance = self._make_instance()
        kustomize_operator = mock.MagicMock()
        kustomize_operator.APP = (
            app_constants.HELM_APP_ISTIO)
        instance.execute_kustomize_updates(
            kustomize_operator)
        kustomize_operator \
            .helm_release_resource_delete \
            .assert_called_once_with(
                self.EXPECTED_HELM_RELEASE)

    @mock.patch(
        'sysinv.common.utils.is_chart_enabled',
        return_value=True)
    def test_kustomize_updates_enabled(
        self, mock_chart_enabled
    ):
        """Test kustomize no-op when enabled."""
        instance = self._make_instance()
        kustomize_operator = mock.MagicMock()
        kustomize_operator.APP = (
            app_constants.HELM_APP_ISTIO)
        instance.execute_kustomize_updates(
            kustomize_operator)
        kustomize_operator \
            .helm_release_resource_delete \
            .assert_not_called()


class TestIstioBaseHelm(
    BaseHelmTestMixin, unittest.TestCase
):
    """Tests for IstioBaseHelm."""

    EXPECTED_CHART = (
        app_constants.HELM_CHART_ISTIO_BASE)
    EXPECTED_HELM_RELEASE = (
        app_constants.HELM_CHART_ISTIO_BASE)

    def _get_class(self):
        """Import and return IstioBaseHelm."""
        from k8sapp_istio.helm.istio_base import (
            IstioBaseHelm)
        return IstioBaseHelm


class TestIstioCniHelm(
    BaseHelmTestMixin, unittest.TestCase
):
    """Tests for IstioCniHelm."""

    EXPECTED_CHART = (
        app_constants.HELM_CHART_ISTIO_CNI)
    EXPECTED_HELM_RELEASE = (
        app_constants.HELM_CHART_ISTIO_CNI)

    def _get_class(self):
        """Import and return IstioCniHelm."""
        from k8sapp_istio.helm.istio_cni import (
            IstioCniHelm)
        return IstioCniHelm


class TestIstioPilotHelm(
    BaseHelmTestMixin, unittest.TestCase
):
    """Tests for IstioPilotHelm."""

    EXPECTED_CHART = (
        app_constants.HELM_CHART_ISTIO_PILOT)
    EXPECTED_HELM_RELEASE = (
        app_constants.HELM_CHART_ISTIO_PILOT)

    def _get_class(self):
        """Import and return IstioPilotHelm."""
        from k8sapp_istio.helm.istio_pilot import (
            IstioPilotHelm)
        return IstioPilotHelm


class TestIstioIngressGatewayHelm(
    BaseHelmTestMixin, unittest.TestCase
):
    """Tests for IstioIngressGatewayHelm."""

    EXPECTED_CHART = (
        app_constants
        .HELM_CHART_ISTIO_INGRESSGATEWAY)
    EXPECTED_HELM_RELEASE = (
        app_constants
        .HELM_CHART_ISTIO_INGRESSGATEWAY)

    def _get_class(self):
        """Import and return the class."""
        from k8sapp_istio.helm \
            .istio_ingressgateway import (
                IstioIngressGatewayHelm)
        return IstioIngressGatewayHelm


class TestIstioEgressGatewayHelm(
    BaseHelmTestMixin, unittest.TestCase
):
    """Tests for IstioEgressGatewayHelm."""

    EXPECTED_CHART = (
        app_constants
        .HELM_CHART_ISTIO_EGRESSGATEWAY)
    EXPECTED_HELM_RELEASE = (
        app_constants
        .HELM_CHART_ISTIO_EGRESSGATEWAY)

    def _get_class(self):
        """Import and return the class."""
        from k8sapp_istio.helm \
            .istio_egressgateway import (
                IstioEgressGatewayHelm)
        return IstioEgressGatewayHelm


class TestKialiHelm(
    BaseHelmTestMixin, unittest.TestCase
):
    """Tests for KialiHelm."""

    EXPECTED_CHART = (
        app_constants.HELM_CHART_KIALI_SERVER)
    EXPECTED_HELM_RELEASE = (
        app_constants.HELM_CHART_KIALI_SERVER)

    def _get_class(self):
        """Import and return KialiHelm."""
        from k8sapp_istio.helm.kiali_server import (
            KialiHelm)
        return KialiHelm
