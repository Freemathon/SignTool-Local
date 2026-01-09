# LocalSignTools

A simplified local-only version of SignTools for signing iOS applications. This version uses only the integrated builder, allowing all signing operations to run entirely on a single machine without requiring external builder servers.

## Overview

LocalSignTools is a streamlined local execution version of SignTools that includes only the integrated builder functionality. External builders and CI/CD services are not required, as all processing runs locally.

## Features

- **Integrated Builder**: Signing operations run internally (no separate server required)
- **Simple Configuration**: Only the integrated version is included, keeping the codebase clean
- **Automatic Port Management**: Automatically uses a random port if the default port is in use
- **Automatic Cleanup**: Automatically removes old upload files
- **2FA Support**: Supports Apple Developer Account two-factor authentication
- **Web Interface**: Easy-to-use browser-based interface

## Requirements

- macOS (required for iOS app signing)
- Go 1.24.0 or higher (for building)
- fastlane (required for signing operations)
- Python 3 (required for signing scripts)
- Node.js (required for signing scripts)

### Installing Dependencies

```bash
# Install fastlane
brew install fastlane
# or
gem install fastlane

# Python 3 and Node.js are typically included with macOS
```

## Setup

### 1. Build the Project

#### Option A: Build .app Bundle (Recommended)

```bash
cd LocalSignTools

# Download dependencies
go mod download

# Build .app bundle (includes building the executable)
./build_app.sh
```

This will create `SignTools.app` which can be double-clicked to launch.

**Note:** You only need to run `build_app.sh` when:
- You modify the source code (`main.go` or files in `src/`)
- You update dependencies (`go.mod`)
- You change the `.app` bundle structure or wrapper script

You do **NOT** need to rebuild when:
- Adding or modifying files in the `data/` folder (profiles, apps, uploads)
- Changing the `signer-cfg.yml` configuration file
- Modifying files in the `builder/` directory

The `data/` folder contents are loaded at runtime, so changes take effect immediately when you restart the application.

#### Option B: Build Executable Only

```bash
cd LocalSignTools

# Download dependencies
go mod download

# Build
go build -o SignTools
```

### 2. Prepare Configuration File

The `signer-cfg.yml` file will be automatically generated on first run. Edit it as needed:

```yaml
builder:
    integrated:
        enable: true
        sign_files_dir: ./builder
        entrypoint: sign.py
        job_timeout_mins: 15
server_url: http://localhost:8080
save_dir: data
cleanup_interval_mins: 5
sign_timeout_mins: 60
```

### 3. Set Up Signing Profiles

Create signing profiles in the `data/profiles/` directory.

#### Developer Account Profile

Place the following files in `data/profiles/developer_account/`:

- `cert.p12`: Certificate file
- `cert_pass.txt`: Certificate password
- `account_name.txt`: Apple Developer Account email address
- `account_pass.txt`: Apple Developer Account password
- `name.txt`: Developer name (e.g., "Tatsuya Kawabata")

#### Custom Provisioning Profile

Place the following files in `data/profiles/custom_profile/`:

- `cert.p12`: Certificate file
- `cert_pass.txt`: Certificate password
- `prov.mobileprovision`: Provisioning profile
- `name.txt`: Profile name

### 4. Set Permissions for Sensitive Files

Restrict permissions on files containing sensitive information:

```bash
chmod 600 data/profiles/*/cert.p12
chmod 600 data/profiles/*/cert_pass.txt
chmod 600 data/profiles/*/account_name.txt
chmod 600 data/profiles/*/account_pass.txt
```

## Usage

### Method 1: Using .app Bundle (Recommended for Double-Click Launch)

1. Build the .app bundle:
```bash
./build_app.sh
```

2. Double-click `SignTools.app` in Finder, or run:
```bash
open SignTools.app
```

The application will launch in a Terminal window. The web interface will be available at `http://localhost:8080` (or a random port if 8080 is in use).

### Method 2: Direct Command Line Execution

```bash
./SignTools
```

### Access Web Interface

Open the following URL in your browser:

```
http://localhost:8080
```

If port 8080 is in use, a random port will be automatically assigned. Check the startup logs to see the actual port number.

## Two-Factor Authentication (2FA)

When 2FA is enabled on your Apple Developer Account, you will be prompted to enter a 2FA code during signing.

### Entering 2FA Code

1. When you start a signing job, a 2FA input screen will appear in the web interface
2. Enter the 2FA code sent by Apple
3. The signing process will continue

### Troubleshooting 2FA

If you're not receiving 2FA codes:

```bash
# Check 2FA configuration
./check_2fa.sh

# Test fastlane authentication directly
./debug_2fa.sh
```

Things to check:
- Is the email address in `account_name.txt` correct?
- Is 2FA enabled on your Apple Developer Account?
- Is your account locked?

## File Management

### Automatic Cleanup

- **Upload Files**: Files older than 60 minutes are automatically deleted
- **Jobs**: Automatically deleted after timeout
- Cleanup runs on startup and periodically (every 5 minutes)

### Manual Cleanup

```bash
# Delete old files in uploads directory
find data/uploads -type f -mtime +1 -delete
```

## Troubleshooting

### Port Already in Use

If the default port (8080) is in use, a random port will be automatically assigned. Check the startup logs to see the actual port number.

### Signing Fails

1. Verify that fastlane is correctly installed
2. Check that certificates and profiles are correctly configured
3. Check the logs (use `-log-level 0` for detailed logs)

```bash
./SignTools -log-level 0
```

### 2FA Codes Not Received

1. Verify the email address in `account_name.txt`
2. Test fastlane authentication with `debug_2fa.sh`
3. Check your Apple Developer Account settings

## Directory Structure

```
LocalSignTools/
├── SignTools                 # Main executable (built)
├── SignTools.app            # macOS .app bundle (built)
├── build_app.sh             # Script to build .app bundle
├── signer-cfg.yml           # Configuration file
├── data/                    # Data directory
│   ├── apps/               # Uploaded applications
│   ├── profiles/           # Signing profiles
│   └── uploads/            # Temporary upload files
├── builder/                # Signing scripts
└── src/                     # Source code
```

## Configuration Details

### Main Settings

- `cleanup_interval_mins`: Cleanup execution interval (minutes)
- `sign_timeout_mins`: Signing timeout (minutes)
- `server_url`: Server URL
- `save_dir`: Data storage directory

### Builder Settings

- `integrated.enable`: Enable/disable integrated builder (always true)
- `integrated.sign_files_dir`: Directory containing signing scripts
- `integrated.entrypoint`: Entry point script
- `integrated.job_timeout_mins`: Job timeout (minutes)

## Security

- Set permissions to `600` for sensitive files (certificates, passwords)
- Designed for local environment use
- Enable Basic authentication if needed

```yaml
basic_auth:
    enable: true
    username: admin
    password: YOUR_PASSWORD
```

## Differences from Original SignTools

LocalSignTools is a simplified version of SignTools with the following features removed:

- GitHub Actions Builder
- Semaphore CI Builder
- Self-hosted Builder (external server)

Only the integrated builder is supported, optimized for local environment use.

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

See the `LICENSE` file for the full license text.

### License Summary

- ✅ **Commercial use**: Allowed
- ✅ **Modification**: Allowed
- ✅ **Distribution**: Allowed
- ✅ **Private use**: Allowed
- ✅ **Patent use**: Allowed
- ❌ **Sublicensing**: Not allowed
- ❌ **Liability**: No warranty provided
- ⚠️ **Copyleft**: Modifications must be released under the same license
- ⚠️ **Network use**: If you modify and run on a server, you must provide source code to users

This project is based on [SignTools](https://github.com/SignTools/SignTools), which is also licensed under AGPL-3.0.

## Special Thanks

This project is based on [SignTools](https://github.com/SignTools/SignTools), an open-source iOS app signing tool. LocalSignTools is a simplified local-only version that maintains compatibility with the original project's signing infrastructure while focusing on ease of use for local development.

We would like to express our gratitude to the original SignTools project and its contributors for creating an excellent foundation for iOS app signing workflows.

## Contributing

This is a local-only version focused on simplicity. For contributions to the main SignTools project, please refer to the [original repository](https://github.com/SignTools/SignTools).
