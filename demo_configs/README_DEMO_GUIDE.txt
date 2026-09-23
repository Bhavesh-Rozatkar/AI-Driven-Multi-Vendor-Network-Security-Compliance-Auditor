# Cisco Packet Tracer Demo Configuration Guide

## Purpose

Create three Cisco IOS router configuration files for the Cisco CIS Compliance Auditor prototype:

1. `01_compliance_pass.txt` — selected CIS controls are configured to satisfy the benchmark requirements.
2. `02_compliance_fail.txt` — selected CIS controls are deliberately configured incorrectly or omitted.
3. `03_unknown_configuration.txt` — contains benchmark-relevant settings plus configuration properties that do not directly map to a specific supplied CIS control.

The supplied CIS benchmark is the source of truth. The detailed benchmark tables contain the individual controls for AAA, Access, Banners, Password, SNMP, SSH & Services, Logging, NTP, Loopback, Routing, Border Filtering, EIGRP, OSPF and BGP.

## Important

Packet Tracer does not implement every IOS/IOS-XE feature in the supplied benchmark. These demo files therefore focus on controls that are practical to demonstrate in a Packet Tracer router.

Do not expect every CIS control to be evaluated as PASS/FAIL from these files.

## Part A — Create the PASS configuration in Packet Tracer

### 1. Create the topology

1. Open Cisco Packet Tracer.
2. Add one Cisco router. A common Packet Tracer router such as a 2911 can be used.
3. You do not need a switch for the configuration-only demonstration.
4. Open the router and select the **CLI** tab.
5. If Packet Tracer asks about the initial configuration dialog, answer `no`.

### 2. Enter privileged mode

```text
enable
configure terminal
```

### 3. Enter the PASS configuration

Copy the commands from `01_compliance_pass.txt` into the router CLI.

If your Packet Tracer router rejects a command, do not replace it with a guessed command. Record the rejected command and continue with the supported controls.

For RSA keys, Packet Tracer may prompt for key generation. Accept the normal prompt.

### 4. Save the configuration

Run:

```text
end
copy running-config startup-config
```

Press Enter when Packet Tracer asks for the destination filename.

### 5. Display the configuration

Run:

```text
show running-config
```

Copy the complete output.

Save it on your computer as:

```text
01_compliance_pass.txt
```

This is the file to upload to the auditor.

---

## Part B — Create the FAIL configuration in Packet Tracer

### 1. Reset the router

Use a fresh router for the cleanest demo.

Alternatively, remove the previous router and add a new one.

### 2. Enter configuration mode

```text
enable
configure terminal
```

### 3. Enter the FAIL configuration

Copy the commands from `02_compliance_fail.txt`.

This configuration deliberately leaves out or violates several requirements, including selected SSH, VTY, password, logging, NTP, and routing-related requirements.

### 4. Save it

```text
end
copy running-config startup-config
```

### 5. Export the running configuration

```text
show running-config
```

Copy the complete output and save it as:

```text
02_compliance_fail.txt
```

Upload this file to the auditor for the FAIL demonstration.

---

## Part C — Create the UNKNOWN configuration in Packet Tracer

### 1. Use a fresh router

Create another router so the demonstration starts from a clean state.

### 2. Enter configuration mode

```text
enable
configure terminal
```

### 3. Enter the UNKNOWN configuration

Copy the commands from `03_unknown_configuration.txt`.

The configuration includes normal security settings but also includes properties such as:

- `ip tcp adjust-mss`
- `ip redirects`
- `ip unreachables`
- a static route
- `ip tcp synwait-time`

These are intentionally included because they are not explicit controls in the supplied benchmark list.

### 4. Save it

```text
end
copy running-config startup-config
```

### 5. Export it

```text
show running-config
```

Copy the complete output and save it as:

```text
03_unknown_configuration.txt
```

---

# Recommended Demo Procedure

Run the three files through the web application in this order.

## Demo 1 — PASS

Upload:

```text
01_compliance_pass.txt
```

Click **Start Audit**.

Show:

- Normalized configuration
- CIS Compliance Summary
- PASS controls
- Evidence/reasons
- Overall summary

## Demo 2 — FAIL

Upload:

```text
02_compliance_fail.txt
```

Click **Start Audit**.

Show:

- Controls changing to FAIL
- Evidence explaining the failure
- Overall compliance degradation
- Risk findings if the application identifies meaningful uncovered risks

## Demo 3 — UNKNOWN / UNCOVERED

Upload:

```text
03_unknown_configuration.txt
```

Click **Start Audit**.

Show the distinction between:

```text
CIS compliance
```

and:

```text
Security risk assessment
```

The important message for the judges is:

> A configuration item not directly covered by the CIS benchmark is not automatically a CIS failure. It can instead be considered separately by the security-risk analysis stage.

---

# Before the SIH Demo

Do one complete dry run of all three files.

Check that:

- Flask starts successfully.
- The Anthropic API key is configured.
- The browser opens the auditor.
- Each configuration uploads successfully.
- Normalization completes.
- CIS evaluation completes.
- Risk analysis completes.
- The final report appears.

Keep these three final text files on the demo laptop so you do not have to rebuild them during the presentation.

## If Packet Tracer rejects commands

Packet Tracer implements only a subset of real Cisco IOS/IOS-XE behavior.

If a command is rejected:

1. Do not invent a replacement.
2. Continue with the controls supported by the router image.
3. Use the resulting `show running-config` as the actual test input.
4. The auditor should use only what is actually present in that exported configuration.

This preserves the project's core rule: the AI must not invent configuration values.
