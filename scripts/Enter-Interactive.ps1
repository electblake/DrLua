<#
.SYNOPSIS
Opens the DrLua WinForms launcher.

.DESCRIPTION
Launches a simple Windows Forms UI for entering DrLua release metadata and then
invokes `dist\drlua.exe` with the selected source path and form values.

If `InputPath` is omitted, the script prompts for a folder.

.PARAMETER InputPath
Optional source folder or file path to pre-load into the launcher.

.EXAMPLE
Get-Help .\scripts\Enter-Interactive.ps1

Shows the help for the launcher script.

.EXAMPLE
.\scripts\Enter-Interactive.ps1 'I:\Sz.Civilians\[Blondes]\Example'

Opens the launcher with the specified source path already selected.

.EXAMPLE
.\scripts\Enter-Interactive.ps1

Opens the launcher and prompts for a source folder first.
#>
[CmdletBinding()]
param (
    [Parameter()]
    [string]$InputPath,

    [Parameter(Mandatory)]
    [string]$DrLuaExe
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

function Get-DefaultReleaseName {
    param(
        [Parameter(Mandatory)]
        [string]$PathValue
    )

    $item = Get-Item -LiteralPath (Resolve-Path -LiteralPath $PathValue).Path
    if ($item.PSIsContainer) {
        return $item.Name
    }

    return $item.BaseName
}

function Get-CategoryProfiles {
    param(
        [Parameter(Mandatory)]
        [System.Collections.IDictionary]$CategoryTable,
        [string[]]$ParentNames = @(),
        [string]$InheritedSection = '',
        [string]$InheritedGroup = '',
        [string]$InheritedPath = '',
        [string[]]$InheritedTags = @()
    )

    $profiles = New-Object System.Collections.Generic.List[object]

    foreach ($entry in $CategoryTable.GetEnumerator()) {
        $name = [string]$entry.Key
        $node = [System.Collections.IDictionary]$entry.Value
        $names = @($ParentNames + $name)
        $section = if ($node.Contains('Section') -and $node.Section) { [string]$node.Section } elseif ($InheritedSection) { $InheritedSection } elseif ($ParentNames.Count -eq 0) { $name } else { '' }
        $group = if ($node.Contains('Group') -and $node.Group) { [string]$node.Group } else { $InheritedGroup }
        $path = if ($node.Contains('Path') -and $node.Path) { [string]$node.Path } else { $InheritedPath }
        $tags = New-Object System.Collections.Generic.List[string]
        $seen = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)

        $nodeTags = if ($node.Contains('Tags') -and $node.Tags) { @($node.Tags) } else { @() }
        foreach ($tag in @($InheritedTags) + $nodeTags) {
            if ($null -eq $tag) {
                continue
            }

            $trimmed = [string]$tag
            $trimmed = $trimmed.Trim()
            if (-not $trimmed) {
                continue
            }

            if ($seen.Add($trimmed)) {
                $null = $tags.Add($trimmed)
            }
        }

        if ($node.Contains('Categories') -and $node.Categories) {
            foreach ($child in Get-CategoryProfiles -CategoryTable $node.Categories -ParentNames $names -InheritedSection $section -InheritedGroup $group -InheritedPath $path -InheritedTags $tags.ToArray()) {
                $null = $profiles.Add($child)
            }
            continue
        }

        $null = $profiles.Add([pscustomobject]@{
                DisplayName = $names -join ' > '
                Section = $section
                Group = $group
                Path = $path
                Tags = $tags.ToArray()
            })
    }

    return $profiles.ToArray()
}

$scriptDir = Split-Path -Parent $PSCommandPath
$drluaExe = (Resolve-Path -LiteralPath $DrLuaExe).Path
$categoriesPath = Join-Path $scriptDir 'Categories.psd1'

$profiles = @()
if (Test-Path -LiteralPath $categoriesPath) {
    $categoriesData = Import-PowerShellDataFile -Path $categoriesPath
    if ($categoriesData.Contains('Categories')) {
        $profiles = @(Get-CategoryProfiles -CategoryTable $categoriesData.Categories | Sort-Object DisplayName)
    }
}

if (-not $InputPath) {
    $folderDialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $folderDialog.Description = 'Select the folder to send to DrLua'
    $folderDialog.ShowNewFolderButton = $false
    if ($folderDialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
        exit 0
    }

    $InputPath = $folderDialog.SelectedPath
}

$resolvedInputPath = (Resolve-Path -LiteralPath $InputPath).Path
$defaultName = Get-DefaultReleaseName -PathValue $resolvedInputPath
$sectionOptions = @('Fansites', 'Civilians', 'Inspired')
foreach ($profile in $profiles) {
    if ($profile.Section -and $sectionOptions -notcontains $profile.Section) {
        $sectionOptions += $profile.Section
    }
}

$matchedProfile = $null
$resolvedInputRoot = $resolvedInputPath.TrimEnd('\', '/')
foreach ($profile in $profiles) {
    if (-not $profile.Path) {
        continue
    }

    $profileRoot = ([string]$profile.Path).TrimEnd('\', '/')
    if ($resolvedInputRoot -eq $profileRoot -or $resolvedInputRoot.StartsWith("$profileRoot\", [System.StringComparison]::OrdinalIgnoreCase)) {
        if ($null -eq $matchedProfile -or $profileRoot.Length -gt $matchedProfile.Path.TrimEnd('\', '/').Length) {
            $matchedProfile = $profile
        }
    }
}

$form = New-Object System.Windows.Forms.Form
$form.Text = 'DrLua Launcher'
$form.StartPosition = 'CenterScreen'
$form.Size = New-Object System.Drawing.Size(640, 680)
$form.MinimumSize = New-Object System.Drawing.Size(640, 680)

$sourceLabel = New-Object System.Windows.Forms.Label
$sourceLabel.Location = New-Object System.Drawing.Point(12, 14)
$sourceLabel.Size = New-Object System.Drawing.Size(100, 20)
$sourceLabel.Text = 'Source Path'
$form.Controls.Add($sourceLabel)

$sourceTextBox = New-Object System.Windows.Forms.TextBox
$sourceTextBox.Location = New-Object System.Drawing.Point(12, 36)
$sourceTextBox.Size = New-Object System.Drawing.Size(520, 24)
$sourceTextBox.ReadOnly = $true
$sourceTextBox.Text = $resolvedInputPath
$form.Controls.Add($sourceTextBox)

$browseButton = New-Object System.Windows.Forms.Button
$browseButton.Location = New-Object System.Drawing.Point(540, 34)
$browseButton.Size = New-Object System.Drawing.Size(72, 28)
$browseButton.Text = 'Browse'
$form.Controls.Add($browseButton)

$categoryLabel = New-Object System.Windows.Forms.Label
$categoryLabel.Location = New-Object System.Drawing.Point(12, 76)
$categoryLabel.Size = New-Object System.Drawing.Size(100, 20)
$categoryLabel.Text = 'Category'
$form.Controls.Add($categoryLabel)

$categoryComboBox = New-Object System.Windows.Forms.ComboBox
$categoryComboBox.Location = New-Object System.Drawing.Point(12, 98)
$categoryComboBox.Size = New-Object System.Drawing.Size(600, 24)
$categoryComboBox.DropDownStyle = [System.Windows.Forms.ComboBoxStyle]::DropDownList
$categoryComboBox.DisplayMember = 'DisplayName'
[void]$categoryComboBox.Items.AddRange($profiles)
$categoryComboBox.Enabled = $profiles.Count -gt 0
$form.Controls.Add($categoryComboBox)

$nameLabel = New-Object System.Windows.Forms.Label
$nameLabel.Location = New-Object System.Drawing.Point(12, 138)
$nameLabel.Size = New-Object System.Drawing.Size(100, 20)
$nameLabel.Text = 'Name'
$form.Controls.Add($nameLabel)

$nameTextBox = New-Object System.Windows.Forms.TextBox
$nameTextBox.Location = New-Object System.Drawing.Point(12, 160)
$nameTextBox.Size = New-Object System.Drawing.Size(300, 24)
$nameTextBox.Text = $defaultName
$form.Controls.Add($nameTextBox)

$sectionLabel = New-Object System.Windows.Forms.Label
$sectionLabel.Location = New-Object System.Drawing.Point(330, 138)
$sectionLabel.Size = New-Object System.Drawing.Size(100, 20)
$sectionLabel.Text = 'Section'
$form.Controls.Add($sectionLabel)

$sectionComboBox = New-Object System.Windows.Forms.ComboBox
$sectionComboBox.Location = New-Object System.Drawing.Point(330, 160)
$sectionComboBox.Size = New-Object System.Drawing.Size(282, 24)
$sectionComboBox.DropDownStyle = [System.Windows.Forms.ComboBoxStyle]::DropDown
[void]$sectionComboBox.Items.AddRange($sectionOptions)
$sectionComboBox.Text = if ($matchedProfile) { $matchedProfile.Section } elseif ($sectionOptions.Count -gt 0) { $sectionOptions[0] } else { '' }
$form.Controls.Add($sectionComboBox)

$groupLabel = New-Object System.Windows.Forms.Label
$groupLabel.Location = New-Object System.Drawing.Point(12, 200)
$groupLabel.Size = New-Object System.Drawing.Size(100, 20)
$groupLabel.Text = 'Group'
$form.Controls.Add($groupLabel)

$groupTextBox = New-Object System.Windows.Forms.TextBox
$groupTextBox.Location = New-Object System.Drawing.Point(12, 222)
$groupTextBox.Size = New-Object System.Drawing.Size(600, 24)
$groupTextBox.Text = if ($matchedProfile) { $matchedProfile.Group } else { '' }
$form.Controls.Add($groupTextBox)

$tagLabel = New-Object System.Windows.Forms.Label
$tagLabel.Location = New-Object System.Drawing.Point(12, 262)
$tagLabel.Size = New-Object System.Drawing.Size(240, 20)
$tagLabel.Text = 'Tags (one per line or comma-separated)'
$form.Controls.Add($tagLabel)

$tagTextBox = New-Object System.Windows.Forms.TextBox
$tagTextBox.Location = New-Object System.Drawing.Point(12, 284)
$tagTextBox.Size = New-Object System.Drawing.Size(600, 140)
$tagTextBox.Multiline = $true
$tagTextBox.AcceptsReturn = $true
$tagTextBox.AcceptsTab = $false
$tagTextBox.ScrollBars = [System.Windows.Forms.ScrollBars]::Vertical
$tagTextBox.Text = if ($matchedProfile) { $matchedProfile.Tags -join [Environment]::NewLine } else { '' }
$form.Controls.Add($tagTextBox)

$sendButton = New-Object System.Windows.Forms.Button
$sendButton.Location = New-Object System.Drawing.Point(12, 438)
$sendButton.Size = New-Object System.Drawing.Size(150, 34)
$sendButton.Text = 'Send to DrLua'
$form.Controls.Add($sendButton)

$statusLabel = New-Object System.Windows.Forms.Label
$statusLabel.Location = New-Object System.Drawing.Point(12, 486)
$statusLabel.Size = New-Object System.Drawing.Size(100, 20)
$statusLabel.Text = 'Output'
$form.Controls.Add($statusLabel)

$outputTextBox = New-Object System.Windows.Forms.TextBox
$outputTextBox.Location = New-Object System.Drawing.Point(12, 508)
$outputTextBox.Size = New-Object System.Drawing.Size(600, 120)
$outputTextBox.Multiline = $true
$outputTextBox.ReadOnly = $true
$outputTextBox.ScrollBars = [System.Windows.Forms.ScrollBars]::Vertical
$outputTextBox.Font = New-Object System.Drawing.Font('Consolas', 9)
$form.Controls.Add($outputTextBox)

$browseButton.Add_Click({
    $folderDialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $folderDialog.Description = 'Select the folder to send to DrLua'
    $folderDialog.ShowNewFolderButton = $false
    $folderDialog.SelectedPath = $sourceTextBox.Text
    if ($folderDialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
        return
    }

    $sourceTextBox.Text = (Resolve-Path -LiteralPath $folderDialog.SelectedPath).Path
    if (-not $nameTextBox.Text.Trim()) {
        $nameTextBox.Text = Get-DefaultReleaseName -PathValue $sourceTextBox.Text
    }

    $selectedProfile = $null
    $selectedRoot = $sourceTextBox.Text.TrimEnd('\', '/')
    foreach ($profile in $profiles) {
        if (-not $profile.Path) {
            continue
        }

        $profileRoot = ([string]$profile.Path).TrimEnd('\', '/')
        if ($selectedRoot -eq $profileRoot -or $selectedRoot.StartsWith("$profileRoot\", [System.StringComparison]::OrdinalIgnoreCase)) {
            if ($null -eq $selectedProfile -or $profileRoot.Length -gt $selectedProfile.Path.TrimEnd('\', '/').Length) {
                $selectedProfile = $profile
            }
        }
    }

    if ($selectedProfile) {
        $categoryComboBox.SelectedItem = $selectedProfile
        $sectionComboBox.Text = $selectedProfile.Section
        $groupTextBox.Text = $selectedProfile.Group
        $tagTextBox.Text = $selectedProfile.Tags -join [Environment]::NewLine
    }
    else {
        $categoryComboBox.SelectedIndex = -1
    }
})

$categoryComboBox.Add_SelectedIndexChanged({
    if (-not $categoryComboBox.SelectedItem) {
        return
    }

    $sectionComboBox.Text = $categoryComboBox.SelectedItem.Section
    $groupTextBox.Text = $categoryComboBox.SelectedItem.Group
    $tagTextBox.Text = $categoryComboBox.SelectedItem.Tags -join [Environment]::NewLine
})

if ($matchedProfile) {
    $categoryComboBox.SelectedItem = $matchedProfile
}

$sendButton.Add_Click({
    $arguments = @($sourceTextBox.Text.Trim())

    if ($nameTextBox.Text.Trim()) {
        $arguments += @('--name', $nameTextBox.Text.Trim())
    }

    if ($sectionComboBox.Text.Trim()) {
        $arguments += @('--section', $sectionComboBox.Text.Trim())
    }

    if ($groupTextBox.Text.Trim()) {
        $arguments += @('--group', $groupTextBox.Text.Trim())
    }

    foreach ($tag in ($tagTextBox.Text -split "[`r`n,]" | ForEach-Object { $_.Trim() } | Where-Object { $_ })) {
        $arguments += @('--tag', $tag)
    }

    $preview = foreach ($argument in $arguments) {
        if ($argument -match '\s|"') {
            '"' + ($argument -replace '"', '\"') + '"'
        }
        else {
            $argument
        }
    }

    $sendButton.Enabled = $false
    $form.UseWaitCursor = $true
    $outputTextBox.Text = "Running:`r`n$drluaExe $($preview -join ' ')`r`n`r`n"
    $outputTextBox.AppendText((( & $drluaExe @arguments 2>&1 | Out-String ).TrimEnd() + "`r`n"))
    $form.UseWaitCursor = $false
    $sendButton.Enabled = $true
})

[void]$form.ShowDialog()
