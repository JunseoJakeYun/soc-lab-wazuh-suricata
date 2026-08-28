#!/usr/bin/env python3

"""
#===========================================================
# SOC LAB - Suricata to Wazuh Alert Filter
# Location : SOC-IDS-01 /usr/local/bin/suricata-wazuh-filter.py
#===========================================================
# Purpose:
#    Monitor Suricata's eve.json file and forward only
#    Suricata alert events to a separate JSON file monitored
#    by the Wazuh Agent.
#
#Data flow:
#
#    Suricata
#        |
#        v
#    eve.json
#        |
#        v
#    This script
#        |
#        | event_type == "alert"
#        v
#    wazuh-alerts.json
#        |
#        v
#    Wazuh Agent
#        |
#        v
#    Wazuh Manager
#        |
#        v
#    Wazuh Dashboard
# """

import json
import time

SOURCE = "/var/log/suricata/eve.json"
DEST = "/var/log/suricata/wazuh-alerts.json"

with open(SOURCE, "r") as source:
    source.seek(0, 2)

    while True:
        line = source.readline()

        if not line:
            time.sleep(0.2)
            continue

        try:
            event = json.loads(line)

            if event.get("event_type") == "alert":
                with open(DEST, "a") as output:
                    json.dump(event, output, separators=(",", ":"))
                    output.write("\n")
                    output.flush()

        except json.JSONDecodeError:
            continue
