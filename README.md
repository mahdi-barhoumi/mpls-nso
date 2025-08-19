# 🌐 MPLS L3VPN Orchestration Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-Django-blue?style=for-the-badge&logo=python&logoColor=white)
![Vue.js](https://img.shields.io/badge/Vue.js-3.0-4fc08d?style=for-the-badge&logo=vue.js&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

</div>

---

## 🔍 Overview

This **open-source platform** automates the full lifecycle of Cisco-based Layer 3 VPN (L3VPN) services over MPLS backbones. Manual L3VPN provisioning is complex and error-prone; this solution streamlines VPN creation, configuration, and monitoring by integrating network discovery, service orchestration, and device provisioning. The backend is modular (Python/Django), and the frontend is a modern Vue.js SPA. Automation reduces operational effort and risk, enabling scalable, reliable network management.

## ✨ Key Features

- **🔍 Automated Network Discovery:** Scans MPLS routers to build a real-time inventory of devices, interfaces, and links.
- **🏗️ L3VPN Service Orchestration:** Create, update, and delete L3VPN instances (VRFs, route targets, interface assignments) via UI or REST API.
- **🚀 Zero-Touch Provisioning (ZTP):** Automated device onboarding using DHCP and TFTP modules.
- **⚙️ Configuration Management:** Push, retrieve, and audit device configurations via NETCONF/RESTCONF with YANG models.
- **📊 Real-Time Monitoring:** Collects metrics, logs, and events for network health and SLA compliance.
- **🎨 Web UI Dashboard:** Responsive Vue.js SPA (PrimeVue/Tailwind) with forms, topology visualization, data tables, and monitoring views.

## 🏗️ Architecture

- **Backend:** Python/Django, modular apps (discovery, DHCP/TFTP ZTP, service orchestrator, network monitor, etc.), REST APIs, SQLite, extensible for new device types/protocols.
- **Frontend:** Vue.js SPA, PrimeVue Sakai theme, Tailwind CSS.
- **Emulation & Lab:** Cisco CSR1000v/vIOSL2 routers (EVE-NG/VMware) emulate MPLS core and customer edges for workflow validation.

## 🚀 Getting Started

### 1️⃣ **Lab Setup:**
- See `docs/lab-config.txt` for instructions to deploy a Cisco-based MPLS topology in EVE-NG or VMware Workstation.

### 2️⃣ **Backend:**
```bash
# Install Python 3 and Django
# Clone the repository, install dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate

# Run the server
python manage.py runserver
```

### 3️⃣ **Frontend:**
```bash
# Install Node.js and npm
# In frontend/, run:
npm install
npm run dev

# Access the UI at http://localhost:5173
```

### 4️⃣ **First-Time Setup:**
- Configure initial network parameters and add devices via the UI or API.
- *Placeholder: Add more details about initial configuration steps here.*

### 5️⃣ **Service Management:**
- Use the dashboard to create/edit/delete L3VPNs, assign interfaces to VRFs, and provision devices. Configurations are pushed automatically and inventory is updated in real time.

### 6️⃣ **Monitoring & Logs:**
- View network status, performance graphs, and event logs directly in the application's UI monitoring/logs page. Backend modules collect live metrics and logs and expose them via the API for visualization and troubleshooting.
- *Placeholder: Add more details about log formats, filtering, and access via the UI here.*

<!-- For more usage details, refer to lab-config.txt and in-code comments. -->

## 🤝 Contributing

**Contributions are welcome!** Developed by [@mahdi-barhoumi](https://github.com/mahdi-barhoumi) and [@Fyroo](https://github.com/Fyroo). 

Please open issues or submit pull requests for bug fixes, features, or improvements. Follow standard GitHub workflow, maintain clear commit history, and include relevant tests or docs. For major changes, discuss via GitHub Issues first.

## 📄 License

Released under the **MIT License**. See LICENSE for details.

## 🙏 Acknowledgements

Special thanks to ???

## 📸 Screenshots

<!-- Add screenshots below -->

<div align="center">

### 🏠 Dashboard
![Dashboard](images/dashboard-placeholder.png)

### ⚙️ Service Creation
![Service Creation](images/service-creation-placeholder.png)

### 📊 Monitoring
![Monitoring](images/monitoring-placeholder.png)

</div>
