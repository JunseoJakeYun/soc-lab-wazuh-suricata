# SSH Brute Force Detection Test

## 1. Objective

The objective of this test is to verify that Wazuh can detect
repeated failed SSH login attempts and identify them as a possible
SSH brute-force attack.

Unlike the network-based Suricata detections, this detection uses
host-based authentication logs collected by the Wazuh Agent.

## 2. Lab Environment

- Target Server: SOC-IDS-01
- Log Source: /var/log/auth.log
- SIEM: Wazuh
- Protocol: SSH
- Port: 22
- Detection Type: Host-Based
- Wazuh Base Rule: 5760
- Custom Correlation Rule: 100200

## 3. Log Collection

The Wazuh Agent monitors the SSH authentication log:

```xml
<localfile>
  <log_format>syslog</log_format>
  <location>/var/log/auth.log</location>
</localfile>
```

This allows Wazuh to receive SSH authentication events from the
server.

## 4. Initial SSH Failure Detection (pre-defined rule by Wazuh)

Wazuh's existing SSH detection rule identifies failed authentication
attempts.

The base rule used for this detection is:

```text
Rule ID: 5760
Level: 5
Description: sshd: authentication failed.
```

Each failed SSH login can therefore generate a Wazuh event matching
rule `5760`.


## 5. Custom SSH Brute Force Correlation Rule

A custom Wazuh rule was created to identify repeated authentication
failures from the same source IP:

```xml
<rule id="100200" level="10" frequency="5" timeframe="120">
  <if_matched_sid>5760</if_matched_sid>
  <same_srcip />
  <description>
    SSH Brute Force Attack - 5 failed login attempts
    from the same source IP within 120 seconds
  </description>
</rule>
```

### Rule Explanation

- **Rule ID:** 100200
- **Level:** 10
- **Base Rule:** 5760
- **Frequency:** 5 events
- **Timeframe:** 120 seconds
- **Correlation:** Same source IP
- **Detection:** Repeated SSH authentication failures

The rule uses the existing SSH authentication failure detection
(rule `5760`) as the trigger for correlation.

## 6. What Does `if_matched_sid` Do?

The following line:

```xml
<if_matched_sid>5760</if_matched_sid>
```

means:

> Only count events that have previously matched Wazuh rule 5760.

Therefore, the custom rule does not detect SSH failures by itself.

The detection works in two stages:

```text
SSH failed login
       ↓
Rule 5760
       ↓
Authentication failure detected
       ↓
5 matching failures
       ↓
Rule 100200
       ↓
SSH Brute Force Attack
```

## 7. Test Procedure

Multiple unsuccessful SSH login attempts were generated against
the SSH service.

Example:

```bash
ssh invaliduser@<TARGET-IP>
```

<img width="609" height="266" alt="sshfailattempts" src="https://github.com/user-attachments/assets/2e3e17d7-2cd0-447a-bbb4-4fab0377ff72" />


The failed authentication attempts generated events in:

```text
/var/log/auth.log
```

The Wazuh Agent collected these events and forwarded them to the
Wazuh Manager.


## 8. Authentication Log Evidence

The failed SSH attempts can be observed in:

```bash
sudo tail -f /var/log/auth.log
```

Example:

```text
Failed password for invalid user ...
Failed password for invalid user ...
Failed password for invalid user ...
```

<img width="1469" height="207" alt="authlog" src="https://github.com/user-attachments/assets/580456d6-8efd-4c5c-9195-7abd1d8a0c9a" />


The screenshot shows the repeated failed SSH authentication
attempts recorded by the operating system.

## 9. Wazuh Detection

After multiple failed SSH authentication attempts from the same
source IP - predefined rule '5760', Wazuh correlated the events using custom rule `100200`.

The resulting alert identifies the activity as:

<img width="1882" height="380" alt="sshfaildashboard" src="https://github.com/user-attachments/assets/17fe4a32-fdf4-4fe4-a2e1-bff46ce85dbb" />


The Wazuh Dashboard displays the correlated SSH brute-force alert.

## 10. Result

**PASS**

The SSH brute-force detection successfully identified repeated
failed SSH authentication attempts from the same source IP.

Wazuh first detected the individual authentication failures using
rule `5760` and then correlated multiple matching events using
custom rule `100200`.

The resulting Level 10 alert was displayed in the Wazuh Dashboard.


## 11. Evidence

The following evidence is included in this repository:

- SSH authentication failure logs
- Wazuh rule `5760`
- Custom Wazuh correlation rule `100200`
- Wazuh brute-force alert
- Wazuh Dashboard screenshot
