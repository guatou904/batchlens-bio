; BuildRoot, RepoRoot and AppVersion are supplied by the native Windows build job.
[Setup]
AppId={{5E869287-05CC-4666-983C-0DAAE9BF5D70}
AppName=BatchLens Bio
AppVersion={#AppVersion}
AppPublisher=BatchLens contributors
AppPublisherURL=https://github.com/guatou904/batchlens-bio
DefaultDirName={localappdata}\Programs\BatchLens Bio
DefaultGroupName=BatchLens Bio
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.19041
UninstallDisplayIcon={app}\BatchLens Bio.exe
SetupIconFile={#BuildRoot}\BatchLens.ico
LicenseFile={#RepoRoot}\LICENSE
OutputDir={#BuildRoot}
OutputBaseFilename=BatchLens-Bio-{#AppVersion}-Windows-x64-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes

[Files]
Source: "{#BuildRoot}\frozen\BatchLens Bio\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "{#BuildRoot}\MicrosoftEdgeWebview2Setup.exe"; Flags: dontcopy

[Icons]
Name: "{group}\BatchLens Bio"; Filename: "{app}\BatchLens Bio.exe"
Name: "{autodesktop}\BatchLens Bio"; Filename: "{app}\BatchLens Bio.exe"; Tasks: desktopicon

[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; Flags: unchecked

[Run]
Filename: "{app}\BatchLens Bio.exe"; Description: "Open BatchLens Bio"; Flags: nowait postinstall skipifsilent

[Code]
function HasRuntimeAt(Root: Integer): Boolean;
var Version: String;
begin
  Result := RegQueryStringValue(Root,
    'Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}',
    'pv', Version) and (Version <> '') and (Version <> '0.0.0.0');
end;

function HasWebView2(): Boolean;
begin
  Result := HasRuntimeAt(HKCU) or HasRuntimeAt(HKLM32) or HasRuntimeAt(HKLM64);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var Code: Integer;
begin
  Result := '';
  if not HasWebView2() then begin
    ExtractTemporaryFile('MicrosoftEdgeWebview2Setup.exe');
    if not Exec(ExpandConstant('{tmp}\MicrosoftEdgeWebview2Setup.exe'), '/silent /install',
      '', SW_HIDE, ewWaitUntilTerminated, Code) then begin
      Result := 'Could not start Microsoft WebView2 setup. Please retry the installer.';
      exit;
    end;
    if not HasWebView2() then
      Result := 'Microsoft WebView2 could not be installed. Connect to the internet and retry. ' +
        'On managed computers, ask your administrator to install the WebView2 Runtime.';
  end;
end;
