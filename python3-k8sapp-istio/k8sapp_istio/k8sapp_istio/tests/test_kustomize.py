#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Unit tests for kustomize modules."""

import unittest
from unittest import mock

import yaml

from k8sapp_istio.common import constants as app_constants
from k8sapp_istio.kustomize.kustomize_istio import \
    IstioFluxCDKustomizeOperator
from k8sapp_istio.kustomize import quoted_str


class TestIstioFluxCDKustomizeOperator(unittest.TestCase):
    """Tests for IstioFluxCDKustomizeOperator."""

    def test_app_constant(self):
        """Test APP is set to istio."""
        self.assertEqual(
            IstioFluxCDKustomizeOperator.APP,
            app_constants.HELM_APP_ISTIO)

    def test_platform_mode_kustomize_updates(self):
        """Test platform_mode_kustomize_updates.

        Verifies the method is a no-op.
        """
        operator = IstioFluxCDKustomizeOperator()
        dbapi = mock.MagicMock()
        result = operator.platform_mode_kustomize_updates(
            dbapi, 'test'
        )
        self.assertIsNone(result)


class TestQuotedStr(unittest.TestCase):
    """Tests for quoted_str and quoted_presenter."""

    def test_quoted_str_is_string(self):
        """Test quoted_str is a string subclass."""
        quoted_value = quoted_str('1.0')
        self.assertIsInstance(quoted_value, str)
        self.assertEqual(quoted_value, '1.0')

    def test_quoted_presenter_yaml_output(self):
        """Test quoted_presenter produces quoted YAML."""
        data = {'version': quoted_str('1.0')}
        output = yaml.dump(
            data, default_flow_style=False
        )
        self.assertIn("'1.0'", output)

    def test_quoted_str_preserves_numeric_string(self):
        """Test numeric strings stay as strings."""
        data = {'port': quoted_str('8080')}
        output = yaml.dump(
            data, default_flow_style=False
        )
        self.assertIn("'8080'", output)
