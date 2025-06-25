# ns-ha-test

Linux Network Namespace Manager with persistent systemd service.

**Version:** v1.3

- ✅ Safe re-runs  
- ✅ Interface move only if needed  
- ✅ IP add only if needed  
- ✅ Systemd service install  
- ✅ "test" pings built-in  
- ✅ Installable as /usr/local/bin/ns-ha-test

---

## Features

- ✅ Create and manage Linux network namespace  
- ✅ Move interface and set IP / default route  
- ✅ Install persistent systemd service  
- ✅ Test namespace pings  
- ✅ Fully automated CLI tool

---

## Install Script 

- ✅ Download Config Setup File
- ✅ curl -O https://raw.githubusercontent.com/stevevoto/NameSpaceSetup/main/setup_namespacev2.py
     or
- ✅ wget https://raw.githubusercontent.com/stevevoto/setupNamespace/main/setup_namespacev2.py
- ✅ chmod +x setup_namespace.py
- ✅ run  python3 setup_namespace install  (installs namespace and test scripts)
- ✅ run  python3 setup_namespace    (default list of commands)
- ✅ run  python3 setup_namespace add (adds namespace for testing)
- ✅ run  python3 setup_namespace test1 (tests namespace ping to internet /or connection)
- ✅ run  python3 setup_namespace test2 (tests namespace iperf to internet iperf-server)
- ✅ run  python3 setup_namespace deletes(deletes namespace)

