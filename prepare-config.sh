#!/bin/bash

apt-get -y --force-yes install git python-pip python-tox libpq-dev python-virtualenv
apt-get -y --force-yes install python-dev build-essential
pip install --upgrade pip
pip install --upgrade virtualenv

rm -rf heat-tests
a=$(cat openrc | grep OS_AUTH_URL | cut -d '=' -f 2 | cut -d "'" -f 2)
b=v2.0
mkdir heat-tests
cd heat-tests
git clone https://github.com/openstack/heat.git
cd heat
git checkout stable/mitaka

cd heat_integrationtests

echo '[DEFAULT]

username = nonadmin
password = nonadmin

admin_username = admin
admin_password = admin

tenant_name = nonadmin
admin_tenant_name = admin

user_domain_name = admin
project_domain_name = admin

instance_type = m1.medium
minimal_instance_type = m1.small

image_ref = TestVM
minimal_image_ref = Test

disable_ssl_certificate_validation = false

build_interval = 4
build_timeout = 1200

network_for_ssh = heat_net
fixed_network_name = heat_net
floating_network_name = heat_net

boot_config_env = heat_integrationtests/scenario/templates/boot_config_none_env.yaml
fixed_subnet_name = someSub

ssh_timeout = 300
ip_version_for_ssh = 4
ssh_channel_timeout = 60

tenant_network_mask_bits = 28

skip_scenario_tests = false
skip_functional_tests = false
skip_functional_test_list = ZaqarWaitConditionTest, ZaqarEventSinkTest, ZaqarSignalTransportTest, RemoteStackTest.test_stack_update, RemoteStacteStackTest.test_stack_resource_validation_fail, RemoteStackTest.test_stack_suspend_resume, RemoteStackTest.test_stack_create_bad_region, test_purge.PurgeTest.test_purge, ReloadOnSighupTest.test_api_cfn_reload_on_sighup, ReloadOnSighupTest.test_api_cloudwatch_on_sighup, ReloadOnSighupTest.test_api_reload_on_sighup, RemoteStackTest.test_stack_create, RemoteStackTest.test_stack_resource_validation_fail

skip_scenario_test_list = AodhAlarmTest.test_alarm, CfnInitIntegrationTest.test_server_cfn_init
skip_test_stack_action_list = ABANDON, ADOPT

volume_size = 1
connectivity_timeout = 140
sighup_timeout = 30
sighup_config_edit_retries = 10

heat_config_notify_script = heat-config-notify'>> heat_integrationtests.conf
echo auth_url = "$a$b" >> heat_integrationtests.conf
cd ..
export uc_url=https://git.openstack.org/cgit/openstack/requirements/plain/upper-constraints.txt?h=stable/mitaka
sed -i~ -e "s,{env:UPPER_CONSTRAINTS_FILE[^ ]*}, $uc_url," tox.ini

tox -eintegration
exit
