# Copyright (c) 2022-2023 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from k8sapp_istio.tests import test_plugins

from sysinv.db import api as dbapi
from sysinv.tests.db import base as dbbase
from sysinv.tests.db import utils as dbutils
from sysinv.tests.helm import base


class IstioTestCase(test_plugins.K8SAppIstioAppMixin,
                    base.HelmTestCaseMixin):

    def setUp(self):
        super(IstioTestCase, self).setUp()
        self.app = dbutils.create_test_app(name='istio')
        self.dbapi = dbapi.get_instance()


class IstioTestCaseDummy(IstioTestCase, dbbase.ProvisionedControllerHostTestCase):
    # without a test zuul will fail
    def test_dummy(self):
        pass
