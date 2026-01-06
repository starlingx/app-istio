#
# Copyright (c) 2025 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

""" System inventory Kustomization resource operator."""

from k8sapp_istio.common import constants as app_constants
from sysinv.helm import kustomize_base as base


class IstioFluxCDKustomizeOperator(base.FluxCDKustomizeOperator):

    APP = app_constants.HELM_APP_ISTIO

    def platform_mode_kustomize_updates(self, dbapi, mode):
        """ Update the top-level kustomization resource list

        Make changes to the top-level kustomization resource list based on the
        platform mode

        :param dbapi: DB api object
        :param mode: mode to control when to update the resource list

        """
        pass
