---
page_type: sample
languages:
- python
products:
- azure
- azure-netapp-files
description: "This project demonstrates how to create a Dual-Protocol Volume for Microsoft.NetApp resource provider using Python SDK." 
---

# Azure NetAppFiles Dual-Protocol SDK Sample for Python

This project demonstrates how to use a Python sample application to create a Dual-Protocol Volume (a Volume that uses both SMB/NFSv3 protocol types) for the Microsoft.NetApp resource provider.

In this sample application we perform the following operations:

- Creation
  - ANF Account
  - Capacity Pool
  - Dual-Protocol Volume
- Deletions
  - Dual-Protocol Volume
  - Capacity Pool
  - ANF Account
			
If you don't already have a Microsoft Azure subscription, you can get a FREE trial account [here](http://go.microsoft.com/fwlink/?LinkId=330212).

## Prerequisites

1. Python (code was built and tested using version 3.9.5)
2. Make sure you comply with the dual-protocol items described [here](https://docs.microsoft.com/en-us/azure/azure-netapp-files/create-volumes-dual-protocol#considerations) before you proceed.
3. Azure Subscription.
4. Subscription needs to have Azure NetApp Files resource provider registered. For more information, see [Register for NetApp Resource Provider](https://docs.microsoft.com/en-us/azure/azure-netapp-files/azure-netapp-files-register).
5. Resource Group created
6. Virtual Network with a delegated subnet to Microsoft.Netapp/volumes resource. For more information, please refer to [Guidelines for Azure NetApp Files network planning](https://docs.microsoft.com/en-us/azure/azure-netapp-files/azure-netapp-files-network-topologies)
7. For this sample Python console application to work we need to authenticate, and the chosen method for this sample is using service principals.
   1. Within an [Azure Cloud Shell](https://docs.microsoft.com/en-us/azure/cloud-shell/quickstart) session, make sure you're logged on at the subscription where you want to be associated with the service principal by default:
        ```bash
        az account show
        ```
   
        If this is not the correct subscription, use:
   
        ```bash
        az account set -s <subscription name or id>  
        ```

    2. Create a service principal using Azure CLI
   
        ```bash
        az ad sp create-for-rbac --sdk-auth
        ```
       >Note: this command will automatically assign RBAC contributor role to the service principal at subscription level, you can narrow down the scope to the specific resource group where your tests will create the resources.

    3. Copy the output content and paste it in a file called azureauth.json and secure it with file system permissions
    4. Set an environment variable pointing to the file path you just created, here is an example with Powershell and bash:
            
        Powershell
   
        ```powershell
        [Environment]::SetEnvironmentVariable("AZURE_AUTH_LOCATION", "C:\sdksample\azureauth.json", "User")
        ```
        Bash

        ```bash
        export AZURE_AUTH_LOCATION=/sdksamples/azureauth.json
        ```
        >Note: for other Azure Active Directory authentication methods for Python, please refer to these [samples](https://github.com/AzureAD/microsoft-authentication-library-for-python/tree/dev/sample). 
8. Active Directory infrastructure setup with one or more DNS servers from the AD domain (usually the Domain Controllers) available in the **same virtual network** where you're setting up Azure NetApp Files. If you want to setup an Active Directory test environment, please refer to [Create a new Windows VM and create a new AD Forest, Domain and DC](https://github.com/Azure/azure-quickstart-templates/tree/master/application-workloads/active-directory/active-directory-new-domain) for a quick setup, then you can create the subnet delegated to Microsoft.Netapp/volumes in the vnet that is created.

# What is example.py doing? 

This sample is dedicated to demonstrate how to create a dual-protocol Volume using an ANF Account name in Azure NetApp Files. Dual-protocol volumes use both SMB and NFSv3 protocol types.
Similar to other ANF SDK examples, the authentication method is based on a service principal. This project will first create an ANF Account with an Active Directory object.
Then a capacity pool is created, and finally a single dual-protocol volume using Standard service level tier. The protocol types of the Volume will then be printed out to showcase the inclusion of both.
When executing this application, the user will be prompted to provide the password for the Active Directory User that has permission to domain join computers in AD.

Finally, all created resources will be deleted via the cleanup process (as long as the appropriate variable in example.py has been set to 'True').

# Contents

| File/folder                 | Description                                                                                                      |
|-----------------------------|------------------------------------------------------------------------------------------------------------------|
| `media\`                    | Folder that contains a screenshot of a successful run.                                                           |
| `src\`                      | Sample source code folder.                                                                                       |
| `src\example.py`            | Sample main file that executes all operations.                                                                   |
| `src\sample_utils.py`       | Sample file that contains authentication functions, all wait functions and other small functions.                |
| `src\resource_uri_utils.py` | Sample file that contains functions to work with URIs, e.g. get resource name from URI (`get_anf_capacitypool`). |
| `src\requirements.txt`      | Sample script required modules.                                                                                  |

# How to run the script

1. Clone it locally
    ```powershell
    git clone https://github.com/Azure-Samples/netappfiles-python-dual-protocol-sdk-sample.git
    ```
1. Change folder to **.\netappfiles-python-dual-protocol-sdk-sample\src**
2. Install any missing dependencies as needed
    ```bash
    pip install -r ./requirements.txt
    ```
    or upgrade dependencies if they already exist
    ```bash
    pip install --upgrade ./requirements.txt
    ```
3. Make sure you have the azureauth.json and its environment variable with the path to it defined (as previously described at [prerequisites](#Prerequisites))
4. Edit file **example.py** and change the variables contents as appropriate (names are self-explanatory).
5. Run the script
    ```powershell
    python example.py
    ```

Sample output
![e2e execution](./media/e2e-execution.png)

# References

- [Azure NetAppFiles SDK Sample for Python](https://docs.microsoft.com/en-us/samples/azure-samples/netappfiles-python-sdk-sample/azure-netappfiles-sdk-sample-for-python/)
- [Azure Active Directory Python Authentication samples](https://github.com/AzureAD/microsoft-authentication-library-for-python/tree/dev/sample)
- [Resource limits for Azure NetApp Files](https://docs.microsoft.com/en-us/azure/azure-netapp-files/azure-netapp-files-resource-limits)
- [Azure Cloud Shell](https://docs.microsoft.com/en-us/azure/cloud-shell/quickstart)
- [Azure NetApp Files documentation](https://docs.microsoft.com/en-us/azure/azure-netapp-files/)
- [Download Azure SDKs](https://azure.microsoft.com/downloads/)
- [Create dual-protocol volumes](https://docs.microsoft.com/en-us/azure/azure-netapp-files/create-volumes-dual-protocol)
- [Troubleshoot dual-protocol volumes](https://docs.microsoft.com/en-us/azure/azure-netapp-files/troubleshoot-dual-protocol-volumes)
 
