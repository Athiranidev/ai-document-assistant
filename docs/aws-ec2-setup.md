# AWS EC2 Infrastructure Setup

**Project:** AI Document Assistant  
**Date:** November 24, 2026  
**Cloud Provider:** Amazon Web Services (AWS)  
**AWS Region:** Asia Pacific (Sydney) – `ap-southeast-2`

## 1. Overview

This document describes the AWS infrastructure setup for deploying the AI Document Assistant application.

The objective is to provision an EC2 instance, configure networking, establish secure SSH access, and prepare the environment for application deployment.

## 2. EC2 Instance Configuration

An Amazon EC2 instance was launched to host the application.

| Configuration | Details |
|---|---|
| Cloud Provider | AWS |
| Service | Amazon EC2 |
| Region | Sydney (`ap-southeast-2`) |
| Operating System | To be verified |
| Instance Type | To be verified |
| Storage Type | To be verified |
| Storage Size | To be verified |
| Instance Status | Launched; status checks pending verification |

## 3. Network Configuration

The EC2 instance was configured to use a public subnet to support external connectivity.

Key networking components:

- VPC: Selected VPC
- Subnet: Public subnet
- Public IPv4: Required for external SSH connectivity
- Internet Gateway: Required for public internet connectivity
- Auto-assign Public IPv4: Verify in EC2 configuration

A public subnet requires a route to an Internet Gateway.

## 4. Security Group Configuration

A Security Group was configured to control inbound traffic to the EC2 instance.

### Inbound Rules

| Type | Protocol | Port | Source |
|---|---|---|---|
| SSH | TCP | 22 | My public IPv4 address (`/32`) |

The SSH rule restricts inbound access to the configured public IPv4 address.

**Security considerations:**

- Avoid allowing SSH access from `0.0.0.0/0`.
- Use a restricted source CIDR.
- Never expose private SSH keys or cloud credentials.
- Update the SSH source rule if the public IP address changes.

## 5. IPv4 and IPv6 Investigation

Public IP connectivity was verified using Linux terminal commands.

### Check public IPv4

```bash
curl -4 https://api.ipify.org
```

### Check public IPv6

```bash
curl -6 https://api64.ipify.org
```

### Inspect local IPv6 configuration

```bash
ip -6 addr show
```

The Linux system showed both temporary and stable global IPv6 addresses.

IPv6 Privacy Extensions can generate temporary addresses for outgoing connections.

For the current EC2 SSH configuration, IPv4 was selected to avoid maintaining an SSH rule tied to a rotating temporary IPv6 address.

## 6. Next Steps

- Verify EC2 instance state and status checks.
- Verify public IPv4 assignment.
- Download and securely store the SSH key pair.
- Configure SSH connectivity.
- Install required application dependencies.
- Deploy the AI Document Assistant application.
- Configure Docker and application services.
- Test application accessibility.

## 7. Important Security Practices

- Never commit `.pem` private keys.
- Never commit AWS access keys or secret keys.
- Keep API keys in environment variables.
- Add `.env` and sensitive files to `.gitignore`.
- Restrict SSH access to trusted IP addresses.


