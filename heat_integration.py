#    Copyright 2016 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import unittest
import logging
import os
from random import randint
import subprocess
from mos_tests.functions import common as common_functions
import pytest
import paramiko
import scp
from mos_tests.functions.base import OpenStackTestCase


logger = logging.getLogger(__name__)



@pytest.mark.undestructive
class HeatFunctionalTests(OpenStackTestCase):
    """Heat scenario and functional tests."""

    def setUp(self):
        super(self.__class__, self).setUp()
        # Get path on node to 'templates' dir
        self.templates_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'templates')
        # Get path on node to 'images' dir
        self.images_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'images')

        self.uid_list = []

    def test_heat_functional(self):
        """Run Heat integration tests (1 controller Neutron)
        Scenario:
            1. Install packages
            2. Clone repo with heat-integration tests
            3. Configure controller (create heat-net and non admin user)
            4. Generate .conf file for tests
            5. Run heat integration tests
        """
        # create shared net with subnet using heat template (net available for others tenants)
        timeout = 20
        pool_name = 'someSub'
        stack_name = 'heat-stack-' + str(randint(1, 0x7fffffff))
        template_content = common_functions.read_template(
            self.templates_dir, 'Heat_integration_resource.yaml')
        uid = common_functions.create_stack(self.heat, stack_name,
                                            template_content)

        self.uid_list.append(uid)
        stacks_id = [s.id for s in self.heat.stacks.list()]
        self.assertIn(uid, stacks_id)
        self.assertTrue(common_functions.check_stack_status(stack_name,
                                                            self.heat,
                                                            'CREATE_COMPLETE',
                                                            timeout))
        #Check net
        sub_net = self.neutron.list_subnets()
        sub_net_names = [x['name'] for x in sub_net['subnets']]
        self.assertIn(pool_name, sub_net_names)

        #Create and activate image
        file_name = 'cirros-0.3.4-x86_64-disk.img.txt'
        image_name = 'Test'

        # Prepare full path to image file. Return e.g.:
        # Like: /root/mos_tests/heat/images/cirros-0.3.4-x86_64-disk.img.txt
        image_link_location = os.path.join(self.images_dir, file_name)

        # Download image on node. Like: /tmp/cirros-0.3.4-x86_64-disk.img
        image_path = common_functions.download_image(image_link_location)

        # Create image in Glance
        image = self.glance.images.create(name=image_name,
                                          os_distro='Cirros',
                                          disk_format='qcow2',
                                          visibility='public',
                                          container_format='bare')
        # Check that status is 'queued'
        if image.status != 'queued':
            raise AssertionError("ERROR: Image status after creation is:"
                                 "[{0}]. "
                                 "Expected [queued]".format(image.status))

        # Put image-file in created Image
        with open(image_path, 'rb') as image_content:
            self.glance.images.upload(image.id, image_content)

        # Check that status of image is 'active'
        self.assertEqual(
            self.glance.images.get(image.id)['status'],
            'active',
            'After creation in Glance image status is [{0}]. '
            'Expected is [active]'
                .format(self.glance.images.get(image.id)['status']))

        # Prerapre ssh sessions
        cmd = "arp -an | grep fuel-pxe | cut -d ')' -f 1 | cut -d '(' -f 2 | awk '(NR == 1)'"
        master = os.popen(cmd).read()
        master =master.strip("\n")

        port = 22
        transport = paramiko.Transport((master, port))
        transport.connect(username='root', password='r00tme')
        sftp = paramiko.SFTPClient.from_transport(transport)

        remotepath = '/root/prepare-config.sh'
        localpath = 'prepare-config.sh'
        sftp.put(localpath, remotepath)
        remotepath = '/root/contr.sh'
        localpath = 'contr.sh'
        sftp.put(localpath, remotepath)
        sftp.close()
        transport.close()

        cmd = "chmod +x contr.sh && ./contr.sh "
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(master, username='root', password='r00tme')
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print "stderr: " , stderr.readline()
        print "pwd: ", stdout.readline()

        ssh.close()
