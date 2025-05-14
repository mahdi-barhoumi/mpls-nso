<template>
  <div class="card">
    <div class="grid">
      <div class="col-12">
        <h1 class="text-3xl mb-4">Application Guide</h1>

        <!-- Table of Contents -->
        <div class="mb-4">
          <TabMenu
            :model="sections.map((s) => ({ label: s.title, command: () => scrollTo(s.id) }))"
          />
        </div>

        <!-- Guide Sections -->
        <ScrollPanel class="guide-scroll custom-scrollbar">
          <div v-for="(section, index) in sections" :key="index" :id="section.id" class="mb-4">
            <Card>
              <template #title>
                <div class="flex align-items-center">
                  <i class="pi pi-book mr-2"></i>
                  <h2 class="text-2xl">{{ section.title }}</h2>
                </div>
              </template>
              <template #content>
                <div class="space-y-4">
                  <div v-for="(content, cIndex) in section.content" :key="cIndex">
                    <h3 v-if="content.subtitle" class="text-xl font-medium mb-2">
                      {{ content.subtitle }}
                    </h3>
                    <p class="mb-2 text-color">{{ content.description }}</p>
                    <ul v-if="content.steps" class="list-none p-0 m-0">
                      <li v-for="(step, sIndex) in content.steps" :key="sIndex" class="mb-2">
                        <div class="flex align-items-center">
                          <i class="pi pi-chevron-right mr-2"></i>
                          <span>{{ step }}</span>
                        </div>
                      </li>
                    </ul>
                  </div>
                </div>
              </template>
            </Card>
          </div>
        </ScrollPanel>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const sections = [
  {
    id: 'getting-started',
    title: 'Getting Started',
    content: [
      {
        subtitle: 'Initial Setup',
        description:
          'Before using the application, you need to complete the initial setup process:',
        steps: [
          'Navigate to the setup page when first accessing the application',
          'Configure your network settings and credentials',
          'Set up the administrator account',
          'Configure TFTP and DHCP server settings if needed',
        ],
      },
    ],
  },
  {
    id: 'customer-management',
    title: 'Customer Management',
    content: [
      {
        subtitle: 'Adding New Customers',
        description: 'To add a new customer to the system:',
        steps: [
          'Go to the Customers page from the main menu',
          'Click on "Add New Customer"',
          'Fill in the required information (name, contact details, etc.)',
          'Save the customer information',
        ],
      },
      {
        subtitle: 'Managing Customer Sites',
        description: 'Each customer can have multiple sites:',
        steps: [
          'Navigate to the Sites page',
          'Select the customer from the dropdown',
          'Add or modify site information including location and network details',
          'Configure site-specific VPN settings if required',
        ],
      },
    ],
  },
  {
    id: 'vpn-configuration',
    title: 'VPN Configuration',
    content: [
      {
        description: 'The VPN management system allows you to:',
        steps: [
          'Create and manage VPN configurations',
          'Set up site-to-site VPN connections',
          'Configure VPN policies and security settings',
          'Monitor VPN status and performance',
        ],
      },
    ],
  },
  {
    id: 'network-discovery',
    title: 'Network Discovery',
    content: [
      {
        description: 'The network discovery feature helps you:',
        steps: [
          'Automatically detect devices on the network',
          'Map network topology',
          'Identify device configurations and capabilities',
          'Monitor network health and status',
        ],
      },
    ],
  },
  {
    id: 'dhcp-management',
    title: 'DHCP Management',
    content: [
      {
        description: 'DHCP server configuration and management:',
        steps: [
          'Configure DHCP pools and ranges',
          'Set up DHCP options and policies',
          'View active DHCP leases',
          'Manage IP address assignments',
        ],
      },
    ],
  },
  {
    id: 'tftp-services',
    title: 'TFTP Services',
    content: [
      {
        description: 'Managing TFTP server functionality:',
        steps: [
          'Upload configuration files and firmware images',
          'Manage file permissions and access',
          'Configure automatic configuration deployment',
          'Monitor file transfer status',
        ],
      },
    ],
  },
  {
    id: 'monitoring-logs',
    title: 'Monitoring and Logs',
    content: [
      {
        description: 'System monitoring and log management:',
        steps: [
          'View system logs and events',
          'Monitor device status and health',
          'Track configuration changes',
          'Generate reports and analytics',
        ],
      },
    ],
  },
]

const scrollTo = (id) => {
  const element = document.getElementById(id)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth' })
  }
}
</script>

<style lang="scss" scoped>
.guide-scroll {
  height: calc(100vh - 350px) !important;
  margin-bottom: 2rem;
}

.custom-scrollbar {
  .p-scrollpanel-wrapper {
    border-right: none;
  }

  .p-scrollpanel-bar {
    background-color: var(--primary-color);
    opacity: 0.3;

    &:hover {
      opacity: 0.5;
    }
  }
}

::v-deep(.p-card) {
  margin-bottom: 2rem;
  background: var(--surface-card);

  .p-card-title {
    color: var(--surface-900);
  }

  .p-card-content {
    padding: 1.25rem;
  }
}

.text-color {
  color: var(--text-color);
}
</style>
