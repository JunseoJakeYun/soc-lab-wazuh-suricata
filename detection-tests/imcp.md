# ICMP Detection Test

## Objective

Test that Suricata can detect ICMP echo requests and that the
alert is successfully forwarded to Wazuh and displayed in the
Wazuh Dashboard.

## Lab Environment

- IDS Server: SOC-IDS-01
- IDS: Suricata
- SIEM: Wazuh
- Source: 192.168.0.4
- Destination: 172.16.0.4
- Protocol: ICMP

## Detection Rule

Suricata uses the following custom rule:

alert icmp any any -> $HOME_NET any
(msg:"SOC LAB - ICMP Echo Request Detected";
sid:1000001;
rev:1;)

### Rule Explanation

- **Protocol:** ICMP
- **Source:** Any
- **Destination:** `$HOME_NET`
- **Message:** SOC LAB - ICMP Echo Request Detected
- **SID:** 1000001
- **Revision:** 1

## 4. Test Procedure

An ICMP ping was generated towards the destination server:
<img width="671" height="191" alt="pingtodestination" src="https://github.com/user-attachments/assets/da26b12e-2611-4cef-8a7e-db3eb0311887" />

The ping generated ICMP echo request packets that were inspected by Suricata.

## 5. Suricata Detection

Suricata generated an alert when the ICMP traffic matched the custom rule

Example alert:

#From eve.json
<img width="1890" height="191" alt="suricatadetecticmp2" src="https://github.com/user-attachments/assets/93a7c595-1b45-46b2-8a3a-02166de882d7" />

#From fast.log
<img width="1494" height="99" alt="suricatadetecticmp" src="https://github.com/user-attachments/assets/8a5eea36-3e40-4201-9bbe-c60e9848319c" />



## 6. Suricata to Wazuh Integration

A custom Python service monitors `eve.json` and filters events where:
event_type = alert

The filtered alerts are written to:
/var/log/suricata/wazuh-alerts.json


The Wazuh Agent monitors this file and forwards the events to the Wazuh Manager.

## 7. Wazuh Agent

The Wazuh Agent on `SOC-IDS-01` monitors the filtered Suricata alert file using:

<localfile>
  <log_format>json</log_format>
  <location>/var/log/suricata/wazuh-alerts.json</location>
</localfile>


The Agent forwards the event to the Wazuh Manager over TCP port 1514.


## 8. Wazuh Dashboard

The Suricata alert was successfully received by Wazuh and displayed in the Wazuh Dashboard.
<img width="1421" height="176" alt="dashboardicmp" src="https://github.com/user-attachments/assets/d6fecb5f-9965-4c76-a628-1ee40857bceb" />


The dashboard shows the Suricata-generated ICMP alert and associated event information.


## 9. Result

**PASS**

The ICMP detection was successfully tested end-to-end.

The ICMP traffic was detected by Suricata, filtered by the custom
Python service, collected by the Wazuh Agent, processed by the
Wazuh Manager, and displayed in the Wazuh Dashboard.



## 10. Evidence

The following evidence is included in this repository:

- Suricata ICMP alert
- Wazuh Dashboard alert
- Custom Suricata detection rule
- Wazuh Agent configuration
- Suricata-to-Wazuh Python filtering script
