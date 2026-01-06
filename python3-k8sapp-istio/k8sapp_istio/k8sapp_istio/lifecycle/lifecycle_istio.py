#
# Copyright (c) 2022-2025 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
# All Rights Reserved.
#

""" System inventory App lifecycle operator."""

import os

from k8sapp_istio.common import constants as app_constants
from oslo_log import log as logging
from sysinv.common import constants
from sysinv.common import exception
from sysinv.common import kubernetes
from sysinv.common import utils as cutils
from sysinv.helm import lifecycle_base as base
from sysinv.helm.lifecycle_constants import LifecycleConstants
import yaml

LOG = logging.getLogger(__name__)


class IstioAppLifecycleOperator(base.AppLifecycleOperator):
    def app_lifecycle_actions(self, context, conductor_obj, app_op, app, hook_info):
        """Perform lifecycle actions for an operation

        :param context: request context, can be None
        :param conductor_obj: conductor object, can be None
        :param app_op: AppOperator object
        :param app: AppOperator.Application object
        :param hook_info: LifecycleHookInfo object

        """
        if hook_info.lifecycle_type == LifecycleConstants.APP_LIFECYCLE_TYPE_FLUXCD_REQUEST:
            if hook_info.operation == constants.APP_APPLY_OP:
                if hook_info.relative_timing == LifecycleConstants.APP_LIFECYCLE_TIMING_POST:
                    return self.post_apply(app_op, app, hook_info)

        if hook_info.lifecycle_type == LifecycleConstants.APP_LIFECYCLE_TYPE_RESOURCE:
            if hook_info.operation == constants.APP_UPDATE_OP:
                if hook_info.relative_timing == LifecycleConstants.APP_LIFECYCLE_TIMING_PRE:
                    return self.pre_update(app)

        super(IstioAppLifecycleOperator, self).app_lifecycle_actions(
            context, conductor_obj, app_op, app, hook_info
        )

    def post_apply(self, app_op, app, hook_info):
        LOG.info(
            "Application apply is being called for {} app".format(app_constants.HELM_APP_ISTIO))
        if LifecycleConstants.EXTRA not in hook_info:
            raise exception.LifecycleMissingInfo("Missing {}".format(LifecycleConstants.EXTRA))
        if LifecycleConstants.RETURN_CODE not in hook_info[LifecycleConstants.EXTRA]:
            raise exception.LifecycleMissingInfo(
                "Missing {} {}".format(LifecycleConstants.EXTRA, LifecycleConstants.RETURN_CODE))

        # raise a specific exception to be caught by the
        # retry decorator and attempt a re-apply
        if not hook_info[LifecycleConstants.EXTRA][LifecycleConstants.RETURN_CODE] and \
                not app_op.is_app_aborted(app.name):
            LOG.info("%s app failed applying. Retrying." % str(app.name))
            raise exception.ApplicationApplyFailure(name=app.name)

        dbapi_instance = app_op._dbapi
        db_app_id = dbapi_instance.kube_app_get(app.name).id

        client_core = app_op._kube._get_kubernetesclient_core()
        component_constant = app_constants.HELM_COMPONENT_LABEL_ISTIO

        # chart overrides
        chart_overrides = self._get_helm_user_overrides(
            dbapi_instance,
            db_app_id)

        override_label = {}

        # Namespaces variables
        namespace = client_core.read_namespace(app_constants.HELM_NS_ISTIO_SYSTEM)

        # Old namespace variable
        old_namespace_label = (namespace.metadata.labels.get(component_constant)
                               if component_constant in namespace.metadata.labels
                               else None)

        if component_constant in chart_overrides:
            # User Override variables
            dict_chart_overrides = yaml.safe_load(chart_overrides)
            override_label = dict_chart_overrides.get(component_constant)

        if override_label == 'application':
            namespace.metadata.labels.update({component_constant: 'application'})
            app_op._kube.kube_patch_namespace(app_constants.HELM_NS_ISTIO_SYSTEM, namespace)
        elif override_label == 'platform':
            namespace.metadata.labels.update({component_constant: 'platform'})
            app_op._kube.kube_patch_namespace(app_constants.HELM_NS_ISTIO_SYSTEM, namespace)
        elif not override_label:
            namespace.metadata.labels.update({component_constant: 'platform'})
            app_op._kube.kube_patch_namespace(app_constants.HELM_NS_ISTIO_SYSTEM, namespace)
        else:
            LOG.info(f'WARNING: Namespace label {override_label} not supported')

        namespace_label = namespace.metadata.labels.get(component_constant)
        if old_namespace_label != namespace_label:
            self._delete_istio_pods(app_op, client_core)

    def pre_update(self, app):
        LOG.info(
            "Executing pre_update for {} app".format(app_constants.HELM_APP_ISTIO)
        )
        # Delete istio-operator.yaml if it exists
        # Scenario of Istio App Update:-
        #  v1 - Istio Operator exists in the fluxcd manifests
        #  v2 - Istio Operator is deprecated and not needed anymore
        #  App is updated from v1 to v2, Old istio-operator.yaml is not needed
        #  This takes care of Kubernetes deployment of Istio Operator
        #  Old Manifests files removal is handled in sysinv, conductor/kube_app.py
        yfile = os.path.join(app.sync_fluxcd_manifest, 'istio-operator/istio-operator.yaml')
        if os.path.exists(yfile):
            cmd = ['kubectl', '--kubeconfig', kubernetes.KUBERNETES_ADMIN_CONF,
                   'delete', '-f', yfile, "--request-timeout=30s"]
            stdout, stderr = cutils.trycmd(*cmd)
            LOG.info("{} app: cmd={} stdout={} stderr={}".format(app.name, cmd, stdout, stderr))
        # Comment out istio-operator.yaml in the kustomization.yaml if it exists
        kust_file = os.path.join(app.sync_fluxcd_manifest, 'istio-operator/kustomization.yaml')
        if os.path.exists(kust_file):
            cmd = ['sed', '-i', '/istio-operator.yaml/s/^/#/g', kust_file]
            stdout, stderr = cutils.trycmd(*cmd)
            LOG.info("{} app: cmd={} stdout={} stderr={}".format(app.name, cmd, stdout, stderr))
        cmd_helm_release = ["kubectl", "--kubeconfig", kubernetes.KUBERNETES_ADMIN_CONF,
                            "patch", "helmrelease", "istio-operator",
                            "-n", "istio-system",
                            "--type=merge", "--field-manager=flux-client-side-apply",
                            "-p", '{"spec": {"suspend": true}}', "--request-timeout=10s"]
        stdout, stderr = cutils.trycmd(*cmd_helm_release)
        LOG.info("{} app: cmd={} stdout={} stderr={}".format(app.name, cmd_helm_release,
                                                            stdout, stderr))
        self.remove_finalizers_crd()

    def _get_helm_user_overrides(self, dbapi_instance, db_app_id):
        try:
            overrides = dbapi_instance.helm_override_get(
                app_id=db_app_id,
                name=app_constants.HELM_CHART_ISTIO_BASE,
                namespace=app_constants.HELM_NS_ISTIO_SYSTEM,
            )
        except exception.HelmOverrideNotFound:
            values = {
                "name": app_constants.HELM_CHART_ISTIO_BASE,
                "namespace": app_constants.HELM_NS_ISTIO_SYSTEM,
                "db_app_id": db_app_id,
            }
            overrides = dbapi_instance.helm_override_create(values=values)
        return overrides.user_overrides or ""

    def _delete_istio_pods(self, app_op, client_core):
        # pod list
        system_pods = client_core.list_namespaced_pod(app_constants.HELM_NS_ISTIO_SYSTEM)

        # On namespace label change delete pods to force restart
        for pod in system_pods.items:
            app_op._kube.kube_delete_pod(
                name=pod.metadata.name,
                namespace=app_constants.HELM_NS_ISTIO_SYSTEM,
                grace_periods_seconds=0
            )

    def remove_finalizers_crd(self):
        """ Remove finalizers from CustomResourceDefinitions (CRDs)

        This function removes finalizers from istio-operator CRD
        Needed in case of Application update from N to N+1 where
        N is dependent on istio-operator and
        N+1 is not dependent on istio-operator.
        This is needed to avoid the istio-operator CRD being stuck in
        terminating state.
        """
        # Get crd of istiooperator.install.istio.io example-istiocontrolplane
        cmd_crds = ["kubectl", "--kubeconfig", kubernetes.KUBERNETES_ADMIN_CONF, "get", "crd",
                    "-o=jsonpath='{.items[?(@.spec.group==\"install.istio.io\")].metadata.name}'"]

        stdout, stderr = cutils.trycmd(*cmd_crds)
        if not stderr:
            LOG.info("Removing finalizer from istio-system CRD {}".format(stdout))
            crds = stdout.replace("'", "").strip().split(" ")
            for crd_name in crds:
                # Get custom resources based on each istio-system CRD
                cmd_instances = ["kubectl", "--kubeconfig", kubernetes.KUBERNETES_ADMIN_CONF,
                                 "get", "-n", "istio-system", crd_name,
                                 "-o", "name", "--request-timeout=10s"]
                stdout, stderr = cutils.trycmd(*cmd_instances)
                crd_instances = stdout.strip().split("\n")
                if not stderr and crd_instances:
                    for crd_instance in crd_instances:
                        if crd_instance:
                            # Patch each custom resource to remove finalizers
                            patch_cmd = ["kubectl",
                                         "--kubeconfig", kubernetes.KUBERNETES_ADMIN_CONF,
                                         "patch", "-n", "istio-system", crd_instance,
                                         "--type=json",
                                         "-p", '[{"op": "remove", "path": "/metadata/finalizers"}]',
                                         "--request-timeout=10s"]
                            stdout, stderr = cutils.trycmd(*patch_cmd)
                            LOG.debug(f"{crd_instance} \n stdout: {stdout} \n stderr: {stderr}")
        else:
            LOG.error("Error removing finalizers: {stderr}")
