<#
.SYNOPSIS
Creates the ServiceRequests list for the Customer Request Triage Assistant.

.DESCRIPTION
The script is safe to run again. It creates a generic SharePoint list and adds
only fields that do not already exist. Created is a built-in SharePoint field.

PnP PowerShell requires your own Microsoft Entra application client ID for
interactive sign-in. See docs/deployment-guide.md before running the script.

.EXAMPLE
.\provision-ServiceRequests.ps1 `
  -SiteUrl "https://contoso.sharepoint.com/sites/ServiceDesk" `
  -ClientId "00000000-0000-0000-0000-000000000000"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^https://.+\.sharepoint\.com(/.*)?$')]
    [string]$SiteUrl,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-fA-F-]{36}$')]
    [string]$ClientId,

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$ListTitle = 'ServiceRequests'
)

$ErrorActionPreference = 'Stop'

if ($PSVersionTable.PSVersion -lt [version]'7.4.0') {
    throw "PnP.PowerShell requires PowerShell 7.4.0 or later. Current version: $($PSVersionTable.PSVersion)"
}

if (-not (Get-Module -ListAvailable -Name 'PnP.PowerShell')) {
    throw 'PnP.PowerShell is not installed. Run: Install-Module PnP.PowerShell -Scope CurrentUser'
}

Import-Module PnP.PowerShell
Connect-PnPOnline -Url $SiteUrl -Interactive -ClientId $ClientId

try {
    $list = Get-PnPList -Identity $ListTitle -ErrorAction SilentlyContinue

    if ($null -eq $list) {
        Write-Host "Creating list '$ListTitle'..."
        New-PnPList -Title $ListTitle -Template GenericList -OnQuickLaunch | Out-Null
    }
    else {
        Write-Host "List '$ListTitle' already exists; checking its fields..."
    }

    # Title and Created are built in. Keep Title required for clear queue views.
    Set-PnPField -List $ListTitle -Identity 'Title' -Values @{ Required = $true } | Out-Null

    $fieldDefinitions = @(
        @{
            DisplayName = 'Description'
            InternalName = 'RequestDescription'
            Type = 'Note'
            Required = $true
        },
        @{
            DisplayName = 'Requester'
            InternalName = 'Requester'
            Type = 'User'
            Required = $true
        },
        @{
            DisplayName = 'Category'
            InternalName = 'Category'
            Type = 'Choice'
            Choices = @('Access', 'Hardware', 'Software', 'Microsoft 365', 'Network', 'Other')
            Required = $false
        },
        @{
            DisplayName = 'Priority'
            InternalName = 'Priority'
            Type = 'Choice'
            Choices = @('Low', 'Medium', 'High', 'Critical')
            Required = $false
        },
        @{
            DisplayName = 'AISummary'
            InternalName = 'AISummary'
            Type = 'Note'
            Required = $false
        },
        @{
            DisplayName = 'SuggestedReply'
            InternalName = 'SuggestedReply'
            Type = 'Note'
            Required = $false
        },
        @{
            DisplayName = 'Status'
            InternalName = 'Status'
            Type = 'Choice'
            Choices = @('New', 'Awaiting review', 'Approved', 'Needs edit', 'In progress', 'Resolved', 'Closed')
            Required = $true
            DefaultValue = 'New'
        }
    )

    foreach ($definition in $fieldDefinitions) {
        $existingField = Get-PnPField -List $ListTitle -Identity $definition.InternalName -ErrorAction SilentlyContinue

        if ($null -eq $existingField) {
            $parameters = @{
                List = $ListTitle
                DisplayName = $definition.DisplayName
                InternalName = $definition.InternalName
                Type = $definition.Type
                AddToDefaultView = $true
                Required = $definition.Required
            }

            if ($definition.ContainsKey('Choices')) {
                $parameters['Choices'] = $definition.Choices
            }

            Write-Host "Adding field '$($definition.DisplayName)'..."
            Add-PnPField @parameters | Out-Null

            if ($definition.ContainsKey('DefaultValue')) {
                Set-PnPField -List $ListTitle -Identity $definition.InternalName `
                    -Values @{ DefaultValue = $definition.DefaultValue } | Out-Null
            }
        }
        else {
            Write-Host "Field '$($definition.DisplayName)' already exists."
        }
    }

    # Indexed queue filters are more resilient if the prototype grows.
    foreach ($fieldName in @('Category', 'Priority', 'Status')) {
        Set-PnPField -List $ListTitle -Identity $fieldName -Values @{ Indexed = $true } | Out-Null
    }

    Write-Host "Provisioning complete: $SiteUrl/Lists/$ListTitle" -ForegroundColor Green
}
finally {
    Disconnect-PnPOnline
}
