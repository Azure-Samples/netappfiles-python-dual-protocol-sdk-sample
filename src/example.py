# Copyright (c) Microsoft and contributors.  All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import base64
import resource_uri_utils
from azure.mgmt.netapp import AzureNetAppFilesManagementClient
from azure.mgmt.netapp.models import NetAppAccount, CapacityPool, Volume, ExportPolicyRule, ActiveDirectory
from msrestazure.azure_exceptions import CloudError
from getpass import getpass
from sample_utils import console_output, print_header, get_credentials, wait_for_no_anf_resource, wait_for_anf_resource, get_root_ca_cert

# ------------------------------------------IMPORTANT------------------------------------------------------------------
# Setting variables necessary for resources creation - change these to appropriated values related to your environment
# Please NOTE: Resource Group and VNETs need to be created prior to run this code
# ----------------------------------------------------------------------------------------------------------------------

RESOURCE_GROUP_NAME = "<Resource Group Name>"
LOCATION = "<Location>"
VNET_NAME = "<VNET>"
SUBNET_NAME = "<Subnet Name>"
ANF_ACCOUNT_NAME = "<Account Name>"
CAPACITY_POOL_NAME = "<Capacity Pool>"
CAPACITY_POOL_SERVICE_LEVEL = "Standard"
VOLUME_NAME = "<Volume Name>"

# Shared ANF Properties
CAPACITY_POOL_SIZE = 4398046511104  # 4TiB which is minimum size
VOLUME_SIZE = 107374182400  # 100GiB - volume minimum size

# SMB related variables
DOMAIN_JOIN_USERNAME = "aduser"
DNS_LIST = "10.25.4.68" # Please notice that this is a comma-separated string
AD_FQDN = "testdomain.local"
SMB_SERVERNAME_PREFIX = "testsmb" # this needs to be maximum 10 characters in length and during the domain join process a random string gets appended.

ROOT_CA_CERT_FULL_FILEPATH = "./ad-server.cer" # Base64 encoded root ca certificate full file name

# Change this to 'True' to enable cleanup process
CLEANUP_RESOURCES = False


def create_account(anf_client, resource_group_name, anf_account_name, location, domain_join_user_password, root_cert, tags=None):
    """Creates an Azure NetApp Files Account

    Function that creates an Azure NetApp Files Account, which requires building the
    account body object first.

    Args:
        anf_client (AzureNetAppFilesManagementClient): Azure Resource Provider
            Client designed to interact with ANF resources
        resource_group_name (string): Name of the resource group where the
            account will be created
        anf_account_name (string): Name of the Account being created
        location (string): Azure short name of the region where resource will
            be deployed
        tags (object): Optional. Key-value pairs to tag the resource, default
            value is None. E.g. {'cc':'1234','dept':'IT'}

    Returns:
        NetAppAccount: Returns the newly created NetAppAccount resource
    """
    active_directory = ActiveDirectory(username=DOMAIN_JOIN_USERNAME,
                                       password=domain_join_user_password,
                                       domain=AD_FQDN,
                                       dns=DNS_LIST,
                                       smb_server_name=SMB_SERVERNAME_PREFIX,
                                       server_root_ca_certificate=root_cert)

    account_body = NetAppAccount(location=location,
                                 tags=tags,
                                 active_directories=[active_directory])

    return anf_client.accounts.create_or_update(account_body,
                                                resource_group_name,
                                                anf_account_name).result()


def create_capacity_pool(anf_client, resource_group_name, anf_account_name,
                         capacity_pool_name, size, location, tags=None):
    """Creates a capacity pool within an account

    Function that creates a Capacity Pool. Capacity pools are needed to define
    maximum service level and capacity.

    Args:
        anf_client (AzureNetAppFilesManagementClient): Azure Resource Provider
            Client designed to interact with ANF resources
        resource_group_name (string): Name of the resource group where the
            capacity pool will be created, it needs to be the same as the
            Account
        anf_account_name (string): Name of the Azure NetApp Files Account where
            the capacity pool will be created
        capacity_pool_name (string): Name of Capacity pool
        service_level (string): Desired service level for this new capacity
            pool, valid values are "Ultra","Premium","Standard"
        size (long): Capacity pool size, values range from 4398046511104
            (4TiB) to 549755813888000 (500TiB)
        location (string): Azure short name of the region where resource will
            be deployed, needs to be the same as the account
        tags (object): Optional. Key-value pairs to tag the resource, default
            value is None. E.g. {'cc':'1234','dept':'IT'}

    Returns:
        CapacityPool: Returns the newly created capacity pool resource
    """
    capacity_pool_body = CapacityPool(location=location,
                                      service_level=CAPACITY_POOL_SERVICE_LEVEL,
                                      size=size)

    return anf_client.pools.create_or_update(capacity_pool_body,
                                             resource_group_name,
                                             anf_account_name,
                                             capacity_pool_name).result()


def create_volume(anf_client, resource_group_name, anf_account_name,
                  capacity_pool_name, volume_name, volume_size,
                  subnet_id, location, data_protection=None, tags=None):
    """Creates a volume within a capacity pool

    Function that in this example creates a NFSv4.1 volume within a capacity
    pool, as a note service level needs to be the same as the capacity pool.
    This function also defines the volume body as the configuration settings
    of the new volume.

    Args:
        anf_client (AzureNetAppFilesManagementClient): Azure Resource Provider
            Client designed to interact with ANF resources
        resource_group_name (string): Name of the resource group where the
            volume will be created, it needs to be the same as the account
        anf_account_name (string): Name of the Azure NetApp Files Account where
            the capacity pool holding the volume exists
        capacity_pool_name (string): Capacity pool name where volume will be
            created
        volume_name (string): Volume name
        volume_size (long): Volume size in bytes, minimum value is
            107374182400 (100GiB), maximum value is 109951162777600 (100TiB)
        subnet_id (string): Subnet resource id of the delegated to ANF Volumes
            subnet
        location (string): Azure short name of the region where resource will
            be deployed, needs to be the same as the account
        tags (object): Optional. Key-value pairs to tag the resource, default
            value is None. E.g. {'cc':'1234','dept':'IT'}

    Returns:
        Volume: Returns the newly created volume resource
    """
    protocol_types = ["CIFS", "NFSv3"]

    volume_body = Volume(
        usage_threshold=volume_size,
        creation_token=volume_name,
        location=location,
        service_level=CAPACITY_POOL_SERVICE_LEVEL,
        subnet_id=subnet_id,
        protocol_types=protocol_types,
        data_protection=data_protection,
        security_style="ntfs"
    )

    return anf_client.volumes.create_or_update(volume_body,
                                               resource_group_name,
                                               anf_account_name,
                                               capacity_pool_name,
                                               volume_name).result()


def run_example():
    """Azure NetApp Files Dual-Protocol SDK management example"""

    print_header("Azure NetAppFiles Python SDK Samples - Sample project that creates a Dual-Protocol Volume using "
                 "the Azure NetApp Files SDK")

    # Authenticating using service principal, refer to README.md file for requirement details
    credentials, subscription_id = get_credentials()

    console_output("Instantiating a new Azure NetApp Files management client...")
    anf_client = AzureNetAppFilesManagementClient(credentials, subscription_id)
    console_output("Api Version: {}".format(anf_client.api_version))

    #------------------------------------------------------------------------------------------------------
    # Getting Active Directory Identity's password (from identity that has rights to domain join computers)
    #------------------------------------------------------------------------------------------------------
    domain_join_user_password = getpass(prompt="Please type Active Directory's user password that will domain join ANF's SMB server and press [ENTER]:")

    # Fetching root CA cert for dual-protocol use
    cert_content = get_root_ca_cert(ROOT_CA_CERT_FULL_FILEPATH)
    console_output("Encoding certificate contents as base64 string...")
    encoded_cert_content = base64.b64encode(cert_content.encode())

    console_output("Creating ANF Resources...")
    # Creating ANF Primary Account
    console_output("Creating Account...")

    anf_account = None
    try:
        anf_account = create_account(anf_client,
                                     RESOURCE_GROUP_NAME,
                                     ANF_ACCOUNT_NAME,
                                     LOCATION,
                                     domain_join_user_password,
                                     encoded_cert_content.decode())

        console_output("\tAccount successfully created. Resource id: {}".format(anf_account.id))
    except CloudError as ex:
        console_output("An error occurred while creating Account: {}".format(ex.message))
        raise

    # Creating Capacity Pool
    console_output("Creating Capacity Pool...")

    capacity_pool = None
    try:
        capacity_pool = create_capacity_pool(anf_client,
                                             RESOURCE_GROUP_NAME,
                                             anf_account.name,
                                             CAPACITY_POOL_NAME,
                                             CAPACITY_POOL_SIZE,
                                             LOCATION)

        console_output("\tCapacity Pool successfully created. Resource id: {}".format(capacity_pool.id))
    except CloudError as ex:
        console_output("An error occurred while creating Capacity Pool: {}".format(ex.message))
        raise

    # Creating Volume
    console_output("Creating Volume with dual-protocol...")
    subnet_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
        subscription_id, RESOURCE_GROUP_NAME, VNET_NAME, SUBNET_NAME)

    volume = None
    try:
        pool_name = resource_uri_utils.get_anf_capacity_pool(capacity_pool.id)

        volume = create_volume(anf_client,
                               RESOURCE_GROUP_NAME,
                               anf_account.name,
                               pool_name,
                               VOLUME_NAME,
                               VOLUME_SIZE,
                               subnet_id,
                               LOCATION)

        console_output("\tVolume successfully created. Resource id: {}".format(volume.id))
    except CloudError as ex:
        console_output("An error occurred while creating Volume: {}".format(ex.message))
        raise

    console_output("Current Volume protocol types: {}".format(volume.protocol_types))
    console_output("SMB Server FQDN: {}".format(volume.mount_targets[0].smb_server_fqdn))
    console_output("NFS IP Address: {}".format(volume.mount_targets[0].ip_address))

    """
    Cleanup process. For this process to take effect please change the value of
    CLEANUP_RESOURCES global variable to 'True'
    Note: Volume deletion operations at the RP level are executed serially
    """
    if CLEANUP_RESOURCES:
        # The cleanup process starts from the innermost resources down in the hierarchy chain.
        # In this case: Volumes -> Capacity Pools -> Accounts
        console_output("Cleaning up resources")

        # Cleaning up Volumes
        console_output("Deleting Volumes...")

        try:
            volume_ids = [volume.id]
            for volume_id in volume_ids:
                pool_name = resource_uri_utils.get_resource_value(volume_id, "capacityPools")
                volume_name = resource_uri_utils.get_anf_volume(volume_id)
                console_output("\tDeleting {}".format(volume_name))

                anf_client.volumes.delete(RESOURCE_GROUP_NAME,
                                          anf_account.name,
                                          pool_name,
                                          volume_name).wait()

                # ARM Workaround to wait the deletion complete/propagate
                wait_for_no_anf_resource(anf_client, volume_id)
                console_output("\t\tSuccessfully deleted Volume: {}".format(volume_id))
        except CloudError as ex:
            console_output("An error occurred while deleting volumes: {}".format(ex.message))
            raise

        # Cleaning up Capacity Pools
        console_output("Deleting Capacity Pools...")

        try:
            pool_ids = [capacity_pool.id]
            for pool_id in pool_ids:
                pool_name = resource_uri_utils.get_anf_capacity_pool(pool_id)
                console_output("\tDeleting {}".format(pool_name))

                anf_client.pools.delete(RESOURCE_GROUP_NAME,
                                        anf_account.name,
                                        pool_name).wait()

                wait_for_no_anf_resource(anf_client, pool_id)
                console_output("\t\tSuccessfully deleted Capacity Pool: {}".format(pool_id))
        except CloudError as ex:
            console_output("An error occurred while deleting capacity pools: {}".format(ex.message))
            raise

        # Cleaning up Account
        console_output("Deleting Account...")

        try:
            console_output("\tDeleting {}".format(anf_account.name))

            anf_client.accounts.delete(RESOURCE_GROUP_NAME,
                                       anf_account.name).wait()

            console_output("\t\tSuccessfully deleted Account: {}".format(anf_account.id))
        except CloudError as ex:
            console_output("An error occurred while deleting accounts: {}".format(ex.message))
            raise

    console_output("ANF Dual-Protocol sample has completed successfully")


if __name__ == "__main__":
    run_example()
