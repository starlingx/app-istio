#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Unit tests for lifecycle_istio module."""

import unittest
from unittest import mock

from k8sapp_istio.common import constants as app_constants
from k8sapp_istio.lifecycle.lifecycle_istio import (
    IstioAppLifecycleOperator
)
from sysinv.common import constants
from sysinv.common import exception
from sysinv.helm.lifecycle_constants import LifecycleConstants


class TestIstioAppLifecycleOperator(unittest.TestCase):
    """Tests for IstioAppLifecycleOperator."""

    def setUp(self):
        """Set up test fixtures."""
        self.operator = IstioAppLifecycleOperator()
        self.app_op = mock.MagicMock()
        self.app = mock.MagicMock()
        self.app.name = 'istio'
        self.context = mock.MagicMock()
        self.conductor_obj = mock.MagicMock()

    def tearDown(self):
        """Clean up mocks after each test."""
        mock.patch.stopall()

    def _make_hook_info(
        self, lifecycle_type, operation, timing
    ):
        """Create a mock hook_info object.

        lifecycle_type - the lifecycle type constant
        operation - the operation constant
        timing - the relative timing constant

        Returns a mock with lifecycle attributes set.
        """
        hook = mock.MagicMock()
        hook.lifecycle_type = lifecycle_type
        hook.operation = operation
        hook.relative_timing = timing
        return hook


class TestAppLifecycleActions(
    TestIstioAppLifecycleOperator
):
    """Tests for app_lifecycle_actions dispatch."""

    @mock.patch.object(
        IstioAppLifecycleOperator, 'post_apply')
    def test_fluxcd_apply_post_calls_post_apply(
        self, mock_post_apply
    ):
        """Test post_apply called for fluxcd post-apply."""
        hook = self._make_hook_info(
            LifecycleConstants
            .APP_LIFECYCLE_TYPE_FLUXCD_REQUEST,
            constants.APP_APPLY_OP,
            LifecycleConstants
            .APP_LIFECYCLE_TIMING_POST)
        self.operator.app_lifecycle_actions(
            self.context, self.conductor_obj,
            self.app_op, self.app, hook)
        mock_post_apply.assert_called_once_with(
            self.app_op, self.app, hook)

    @mock.patch.object(
        IstioAppLifecycleOperator, 'pre_update')
    def test_resource_update_pre_calls_pre_update(
        self, mock_pre_update
    ):
        """Test pre_update called for resource pre-update."""
        hook = self._make_hook_info(
            LifecycleConstants
            .APP_LIFECYCLE_TYPE_RESOURCE,
            constants.APP_UPDATE_OP,
            LifecycleConstants
            .APP_LIFECYCLE_TIMING_PRE)
        self.operator.app_lifecycle_actions(
            self.context, self.conductor_obj,
            self.app_op, self.app, hook)
        mock_pre_update.assert_called_once_with(
            self.app)

    @mock.patch(
        'sysinv.helm.lifecycle_base'
        '.AppLifecycleOperator'
        '.app_lifecycle_actions')
    def test_unhandled_hook_calls_super(
        self, mock_super_actions
    ):
        """Test unhandled hooks fall through to super."""
        hook = self._make_hook_info(
            LifecycleConstants
            .APP_LIFECYCLE_TYPE_SEMANTIC_CHECK,
            constants.APP_APPLY_OP,
            LifecycleConstants
            .APP_LIFECYCLE_TIMING_PRE)
        self.operator.app_lifecycle_actions(
            self.context, self.conductor_obj,
            self.app_op, self.app, hook)
        mock_super_actions.assert_called_once()


class TestPostApply(TestIstioAppLifecycleOperator):
    """Tests for post_apply method."""

    def _make_post_apply_hook(self, return_code=True):
        """Create hook_info for post_apply.

        return_code - the return code value to set

        Returns a mock hook with EXTRA configured.
        """
        hook = self._make_hook_info(
            LifecycleConstants
            .APP_LIFECYCLE_TYPE_FLUXCD_REQUEST,
            constants.APP_APPLY_OP,
            LifecycleConstants
            .APP_LIFECYCLE_TIMING_POST)
        hook.__contains__ = (
            lambda s, k: k == LifecycleConstants.EXTRA
        )
        hook.__getitem__ = lambda s, k: {
            LifecycleConstants.RETURN_CODE:
                return_code
        }
        return hook

    def _setup_app_op(self):
        """Set up app_op with mocked dbapi and kube.

        Returns tuple of (namespace_obj, kube_client).
        """
        db_app = mock.MagicMock()
        db_app.id = 1
        self.app_op._dbapi.kube_app_get.return_value = (
            db_app
        )

        namespace_obj = mock.MagicMock()
        label_key = (
            app_constants.HELM_COMPONENT_LABEL_ISTIO
        )
        namespace_obj.metadata.labels = {
            label_key: 'platform'
        }
        kube_client = mock.MagicMock()
        kube_client.read_namespace.return_value = (
            namespace_obj
        )
        kube_core = mock.MagicMock()
        kube_core.return_value = kube_client
        self.app_op._kube._get_kubernetesclient_core = (
            kube_core
        )

        return namespace_obj, kube_client

    def test_post_apply_missing_extra_raises(self):
        """Test post_apply raises when EXTRA missing."""
        hook = self._make_hook_info(
            LifecycleConstants
            .APP_LIFECYCLE_TYPE_FLUXCD_REQUEST,
            constants.APP_APPLY_OP,
            LifecycleConstants
            .APP_LIFECYCLE_TIMING_POST)
        hook.__contains__ = lambda s, k: False
        self.assertRaises(
            exception.LifecycleMissingInfo,
            self.operator.post_apply,
            self.app_op, self.app, hook)

    def test_post_apply_missing_return_code_raises(self):
        """Test post_apply raises without RETURN_CODE."""
        hook = self._make_hook_info(
            LifecycleConstants
            .APP_LIFECYCLE_TYPE_FLUXCD_REQUEST,
            constants.APP_APPLY_OP,
            LifecycleConstants
            .APP_LIFECYCLE_TIMING_POST)
        hook.__contains__ = (
            lambda s, k: k == LifecycleConstants.EXTRA
        )
        hook.__getitem__ = lambda s, k: {}
        self.assertRaises(
            exception.LifecycleMissingInfo,
            self.operator.post_apply,
            self.app_op, self.app, hook)

    @mock.patch.object(
        IstioAppLifecycleOperator,
        '_get_helm_user_overrides',
        return_value='')
    @mock.patch.object(
        IstioAppLifecycleOperator,
        '_delete_istio_pods')
    def test_post_apply_failed_retries(
        self, mock_delete_pods, mock_get_overrides
    ):
        """Test post_apply raises on failure."""
        hook = self._make_post_apply_hook(
            return_code=False)
        self.app_op.is_app_aborted.return_value = False
        self.assertRaises(
            exception.ApplicationApplyFailure,
            self.operator.post_apply,
            self.app_op, self.app, hook)

    @mock.patch.object(
        IstioAppLifecycleOperator,
        '_get_helm_user_overrides',
        return_value='')
    @mock.patch.object(
        IstioAppLifecycleOperator,
        '_delete_istio_pods')
    def test_post_apply_success_no_override(
        self, mock_delete_pods, mock_get_overrides
    ):
        """Test post_apply success with no override."""
        hook = self._make_post_apply_hook(
            return_code=True)
        namespace_obj, kube_client = (
            self._setup_app_op()
        )
        self.operator.post_apply(
            self.app_op, self.app, hook)
        self.app_op._kube.kube_patch_namespace \
            .assert_called()

    @mock.patch.object(
        IstioAppLifecycleOperator,
        '_get_helm_user_overrides')
    @mock.patch.object(
        IstioAppLifecycleOperator,
        '_delete_istio_pods')
    def test_post_apply_override_application(
        self, mock_delete_pods, mock_get_overrides
    ):
        """Test post_apply with application override."""
        label_key = (
            app_constants.HELM_COMPONENT_LABEL_ISTIO
        )
        mock_get_overrides.return_value = (
            '{}: application'.format(label_key))
        hook = self._make_post_apply_hook(
            return_code=True)
        namespace_obj, kube_client = (
            self._setup_app_op()
        )
        namespace_obj.metadata.labels = {
            label_key: 'platform'
        }
        self.operator.post_apply(
            self.app_op, self.app, hook)
        self.app_op._kube.kube_patch_namespace \
            .assert_called()
        mock_delete_pods.assert_called_once()

    @mock.patch.object(
        IstioAppLifecycleOperator,
        '_get_helm_user_overrides')
    @mock.patch.object(
        IstioAppLifecycleOperator,
        '_delete_istio_pods')
    def test_post_apply_override_platform(
        self, mock_delete_pods, mock_get_overrides
    ):
        """Test post_apply with platform override."""
        label_key = (
            app_constants.HELM_COMPONENT_LABEL_ISTIO
        )
        mock_get_overrides.return_value = (
            '{}: platform'.format(label_key))
        hook = self._make_post_apply_hook(
            return_code=True)
        namespace_obj, kube_client = (
            self._setup_app_op()
        )
        namespace_obj.metadata.labels = {
            label_key: 'platform'
        }
        self.operator.post_apply(
            self.app_op, self.app, hook)
        self.app_op._kube.kube_patch_namespace \
            .assert_called()

    @mock.patch.object(
        IstioAppLifecycleOperator,
        '_get_helm_user_overrides')
    @mock.patch.object(
        IstioAppLifecycleOperator,
        '_delete_istio_pods')
    def test_post_apply_override_unsupported(
        self, mock_delete_pods, mock_get_overrides
    ):
        """Test post_apply with unsupported override."""
        label_key = (
            app_constants.HELM_COMPONENT_LABEL_ISTIO
        )
        mock_get_overrides.return_value = (
            '{}: unsupported_value'.format(label_key))
        hook = self._make_post_apply_hook(
            return_code=True)
        namespace_obj, kube_client = (
            self._setup_app_op()
        )
        namespace_obj.metadata.labels = {
            label_key: 'platform'
        }
        self.operator.post_apply(
            self.app_op, self.app, hook)

    @mock.patch.object(
        IstioAppLifecycleOperator,
        '_get_helm_user_overrides',
        return_value='')
    @mock.patch.object(
        IstioAppLifecycleOperator,
        '_delete_istio_pods')
    def test_post_apply_aborted_no_retry(
        self, mock_delete_pods, mock_get_overrides
    ):
        """Test post_apply skips retry when aborted."""
        hook = self._make_post_apply_hook(
            return_code=False)
        self.app_op.is_app_aborted.return_value = True
        namespace_obj, kube_client = (
            self._setup_app_op()
        )
        self.operator.post_apply(
            self.app_op, self.app, hook)


class TestPreUpdate(TestIstioAppLifecycleOperator):
    """Tests for pre_update method."""

    @mock.patch.object(
        IstioAppLifecycleOperator,
        'remove_finalizers_crd')
    @mock.patch('sysinv.common.utils.trycmd')
    @mock.patch('os.path.exists')
    def test_pre_update_files_exist(
        self, mock_exists, mock_trycmd,
        mock_remove_finalizers
    ):
        """Test pre_update when operator files exist."""
        mock_exists.return_value = True
        mock_trycmd.return_value = ('', '')
        self.app.sync_fluxcd_manifest = '/tmp/test'
        self.operator.pre_update(self.app)
        self.assertEqual(mock_trycmd.call_count, 3)
        mock_remove_finalizers.assert_called_once()

    @mock.patch.object(
        IstioAppLifecycleOperator,
        'remove_finalizers_crd')
    @mock.patch('sysinv.common.utils.trycmd')
    @mock.patch('os.path.exists')
    def test_pre_update_files_not_exist(
        self, mock_exists, mock_trycmd,
        mock_remove_finalizers
    ):
        """Test pre_update when files do not exist."""
        mock_exists.return_value = False
        mock_trycmd.return_value = ('', '')
        self.app.sync_fluxcd_manifest = '/tmp/test'
        self.operator.pre_update(self.app)
        self.assertEqual(mock_trycmd.call_count, 1)
        mock_remove_finalizers.assert_called_once()


class TestGetHelmUserOverrides(
    TestIstioAppLifecycleOperator
):
    """Tests for _get_helm_user_overrides method."""

    def test_get_overrides_found(self):
        """Test returns user_overrides when found."""
        dbapi = mock.MagicMock()
        override = mock.MagicMock()
        override.user_overrides = 'some: value'
        dbapi.helm_override_get.return_value = override
        result = (
            self.operator._get_helm_user_overrides(
                dbapi, 1))
        self.assertEqual(result, 'some: value')

    def test_get_overrides_not_found_creates(self):
        """Test creates override when not found."""
        dbapi = mock.MagicMock()
        dbapi.helm_override_get.side_effect = (
            exception.HelmOverrideNotFound(
                name='base',
                namespace='istio-system'))
        new_override = mock.MagicMock()
        new_override.user_overrides = None
        dbapi.helm_override_create.return_value = (
            new_override
        )
        result = (
            self.operator._get_helm_user_overrides(
                dbapi, 1))
        self.assertEqual(result, '')
        dbapi.helm_override_create \
            .assert_called_once()

    def test_get_overrides_none_returns_empty(self):
        """Test returns empty when overrides is None."""
        dbapi = mock.MagicMock()
        override = mock.MagicMock()
        override.user_overrides = None
        dbapi.helm_override_get.return_value = override
        result = (
            self.operator._get_helm_user_overrides(
                dbapi, 1))
        self.assertEqual(result, '')


class TestDeleteIstioPods(
    TestIstioAppLifecycleOperator
):
    """Tests for _delete_istio_pods method."""

    def test_delete_pods(self):
        """Test deletes all pods in namespace."""
        kube_client = mock.MagicMock()
        pod_istiod = mock.MagicMock()
        pod_istiod.metadata.name = 'istiod-abc'
        pod_ingress = mock.MagicMock()
        pod_ingress.metadata.name = (
            'istio-ingress-xyz'
        )
        pod_list = mock.MagicMock()
        pod_list.items = [pod_istiod, pod_ingress]
        kube_client.list_namespaced_pod.return_value = (
            pod_list
        )
        self.operator._delete_istio_pods(
            self.app_op, kube_client)
        self.assertEqual(
            self.app_op._kube
            .kube_delete_pod.call_count, 2)

    def test_delete_pods_empty(self):
        """Test handles empty pod list."""
        kube_client = mock.MagicMock()
        pod_list = mock.MagicMock()
        pod_list.items = []
        kube_client.list_namespaced_pod.return_value = (
            pod_list
        )
        self.operator._delete_istio_pods(
            self.app_op, kube_client)
        self.app_op._kube.kube_delete_pod \
            .assert_not_called()


class TestRemoveFinalizersCrd(
    TestIstioAppLifecycleOperator
):
    """Tests for remove_finalizers_crd method."""

    @mock.patch('sysinv.common.utils.trycmd')
    def test_remove_finalizers_success(
        self, mock_trycmd
    ):
        """Test removes finalizers successfully."""
        mock_trycmd.side_effect = [
            ("'istiooperators.install.istio.io'",
             ''),
            ('istiooperator/example', ''),
            ('', ''),
        ]
        self.operator.remove_finalizers_crd()
        self.assertEqual(mock_trycmd.call_count, 3)

    @mock.patch('sysinv.common.utils.trycmd')
    def test_remove_finalizers_crd_error(
        self, mock_trycmd
    ):
        """Test handles error when getting CRDs."""
        mock_trycmd.return_value = (
            '', 'error getting crds')
        self.operator.remove_finalizers_crd()
        mock_trycmd.assert_called_once()

    @mock.patch('sysinv.common.utils.trycmd')
    def test_remove_finalizers_no_instances(
        self, mock_trycmd
    ):
        """Test handles CRD with no instances."""
        mock_trycmd.side_effect = [
            ("'istiooperators.install.istio.io'",
             ''),
            ('', ''),
        ]
        self.operator.remove_finalizers_crd()
        self.assertEqual(mock_trycmd.call_count, 2)

    @mock.patch('sysinv.common.utils.trycmd')
    def test_remove_finalizers_multiple_crds(
        self, mock_trycmd
    ):
        """Test handles multiple CRDs."""
        mock_trycmd.side_effect = [
            ("'crd1 crd2'", ''),
            ('instance1', ''),
            ('', ''),
            ('instance2\ninstance3', ''),
            ('', ''),
            ('', ''),
        ]
        self.operator.remove_finalizers_crd()
        self.assertGreaterEqual(
            mock_trycmd.call_count, 3)

    @mock.patch('sysinv.common.utils.trycmd')
    def test_remove_finalizers_instance_error(
        self, mock_trycmd
    ):
        """Test handles error getting instances."""
        mock_trycmd.side_effect = [
            ("'istiooperators.install.istio.io'",
             ''),
            ('', 'error getting instances'),
        ]
        self.operator.remove_finalizers_crd()
        self.assertEqual(mock_trycmd.call_count, 2)
