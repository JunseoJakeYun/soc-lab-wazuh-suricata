
## 1. SOC Detection Pipeline

The issue occurred between:

```text
eve.json
   |
   v
Python forwarding script
   |
   v
wazuh-alerts.json
```

Suricata itself was still detecting the traffic correctly.

---

## 2. Initial Symptom

After clearing the `eve.json` file, new Suricata alerts were no longer appearing in:

```text
/var/log/suricata/wazuh-alerts.json
```

As a result, the alerts were also not reaching Wazuh.

The important observation was:

```text
Suricata = generating alerts
eve.json = receiving alerts
Python filter = not forwarding new alerts
wazuh-alerts.json = empty
```

This indicated that the problem was not with the Suricata detection rules themselves.

---

## 3. Check Suricata Alerts

I first checked whether Suricata was still generating alerts:

```bash
sudo grep '"event_type":"alert"' /var/log/suricata/eve.json | tail -3
```

Suricata was successfully generating alerts.

For example, the following detections were present:

```text
SOC LAB - ICMP Echo Request Detected
SOC LAB - Possible TCP Port Scan
SOC LAB - Suspicious HTTP Admin Path
```

This confirmed:

```text
Suricata detection = WORKING
```

---

## 4. Check the Python Forwarding Service

The Python forwarding service was checked with:

```bash
sudo systemctl status suricata-wazuh-filter --no-pager
```

The service showed:

```text
Active: active (running)
```

Example:

```text
● suricata-wazuh-filter.service - Suricata to Wazuh Alert Filter
     Loaded: loaded (/etc/systemd/system/suricata-wazuh-filter.service; enabled)
     Active: active (running)
```

At first this was confusing because the service appeared to be running normally.

However, a running service does not necessarily mean that it is reading the correct position in the log file.

---

## 5. Check the Python File Position

I checked the file descriptor used by the Python forwarding process:

```bash
sudo cat /proc/965/fdinfo/3
```

Output:

```text
pos:    11599185
flags:  02100000
mnt_id: 27
ino:    262500
```

The important value was:

```text
pos: 11599185
```

This showed that the Python process had a file position of approximately **11.6 MB**.

I then checked the current `eve.json` file:

```bash
sudo ls -li /var/log/suricata/eve.json
```

The inode was:

```text
262500
```

The file size was approximately **3.7 MB**.

This gave an important indication:

```text
Python file position:  ~11.6 MB
eve.json size:          ~3.7 MB
inode:                  262500
```

The Python process was therefore holding the same `eve.json` inode but its read position was beyond the current file size.

This was consistent with the earlier manual truncation of `eve.json`.

---

## 6. Why `truncate` Caused the Problem

The command:

```bash
sudo truncate -s 0 /var/log/suricata/eve.json
```

sets the file size to zero.

However, the Python process already had `eve.json` open.

The Python process still had its existing file position.

Conceptually, the situation became:

```text
Before truncate:

eve.json
|------------------------------------|
0                                EOF
                                 ^
                                 |
                          Python position


After truncate:

eve.json
|
EOF

Python process:
                                      ^
                                      |
                            old file position
```

The file was shortened to zero bytes, but the Python process still had an open file descriptor with its previous position.

Suricata then started writing new events from the beginning of the newly truncated file.

The Python process was still waiting at its previous position.

Therefore, it could fail to see the new data being written near the beginning of the file.

---

## 7. The Important Difference

The problem was **not**:

```text
Suricata stopped
```

The problem was **not**:

```text
Suricata rules stopped working
```

The problem was **not**:

```text
Wazuh Manager network connection failed
```

The actual issue was:

```text
eve.json was truncated while the Python script
already had the file open.
```

The Python process retained its existing file position.

---

## 8. Resolution

The simplest resolution was to restart the Python forwarding service:

```bash
sudo systemctl restart suricata-wazuh-filter
```

Then verify that it was running:

```bash
sudo systemctl status suricata-wazuh-filter --no-pager
```

Expected result:

```text
Active: active (running)
```

The restart caused Python to:

1. Close the old file descriptor.
2. Reopen `eve.json`.
3. Execute `source.seek(0, 2)`.
4. Move to the current end of the file.
5. Continue monitoring new Suricata events.

---

## 9. Generate a New Detection

After restarting the service, I generated new test traffic.

For example, an ICMP test:

```bash
ping -c 4 172.16.0.4
```

Then I checked Suricata:

```bash
sudo grep '"event_type":"alert"' /var/log/suricata/eve.json | tail -3
```

The alert was successfully generated.

I then checked the filtered Wazuh file:

```bash
sudo grep "SOC LAB" /var/log/suricata/wazuh-alerts.json | tail
```

The alert was now successfully captured.

This confirmed that the forwarding pipeline was working again.

---


# 10. Root Cause

### Root Cause

The root cause was manually truncating an actively monitored Suricata log file:

```bash
sudo truncate -s 0 /var/log/suricata/eve.json
```

while the Python forwarding script already had the file open.

The Python script maintains a file position and uses:

```python
source.seek(0, 2)
```

when it starts.

After the file was truncated, the Python process continued using its existing file descriptor and file position.

This caused the forwarding script to stop seeing the newly written events correctly.

---

# 11. How to Prevent This in the Future

Avoid manually truncating an actively monitored log file:

```bash
sudo truncate -s 0 /var/log/suricata/eve.json
```

during normal testing.

If the file needs to be cleared for a lab test, restart the forwarding service afterwards:

```bash
sudo systemctl restart suricata-wazuh-filter
```

Then verify:

```bash
sudo systemctl status suricata-wazuh-filter --no-pager
```

After that, generate a new test event and verify the destination file.

---

# 12. Lessons Learned

This troubleshooting exercise provided several practical lessons.

### 1. Do not assume the service is broken

The Python service showed:

```text
Active: active (running)
```

but it was still not forwarding events.

A service being "running" does not always mean that the application is functioning correctly.

---

### 2. Troubleshoot the pipeline from source to destination

Instead of immediately changing Wazuh configuration, I checked:

```text
Suricata
   ↓
eve.json
   ↓
Python filter
   ↓
wazuh-alerts.json
   ↓
Wazuh Agent
   ↓
Wazuh Manager
   ↓
Dashboard
```

This made it possible to isolate the problem.

---

### 3. Check the actual evidence

The following command proved that Suricata was working:

```bash
sudo grep '"event_type":"alert"' /var/log/suricata/eve.json | tail
```

The following command showed that the filtered file was not receiving events:

```bash
sudo grep "SOC LAB" /var/log/suricata/wazuh-alerts.json | tail
```

Comparing both files helped identify where the pipeline was failing.

---

### 4. Understand file descriptors

Using:

```bash
sudo lsof -p <PID>
```

showed that the Python process still had:

```text
/var/log/suricata/eve.json
```

open.

This was an important clue.

---

### 5. Be careful when modifying active log files

Manually clearing an active log file can affect applications that are already reading it.

In a production environment, log rotation should normally be handled using an appropriate log management process rather than manually truncating files.

---

# 13. SOC Analyst Takeaway

This was a useful troubleshooting exercise because the issue was not immediately obvious.

The alert was successfully detected by Suricata, but it was not reaching Wazuh.

The investigation required checking each stage of the detection pipeline and using Linux troubleshooting tools such as:

```bash
grep
systemctl
lsof
ls
stat
/proc/<PID>/fd/
```

The key finding was that `eve.json` had been truncated while the Python forwarding process was already monitoring the file.

Restarting the forwarding service recreated the file descriptor and restored normal alert forwarding.

This demonstrates the importance of:

- Understanding how Linux processes interact with files
- Checking file descriptors
- Troubleshooting from source to destination
- Validating each stage of a SIEM/IDS pipeline
- Avoiding assumptions based only on service status
- Documenting root cause and recovery steps
