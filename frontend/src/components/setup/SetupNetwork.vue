<template>
  <div
    class="bg-surface-0 dark:bg-surface-900 py-2 px-2 sm:px-4 rounded-2xl w-full max-w-full md:max-w-5xl mx-auto pb-0"
  >
    <div
      v-if="networkSettingsExist"
      class="flex flex-col items-center justify-center text-center py-6"
    >
      <i class="pi pi-cog text-4xl text-primary mb-4"></i>
      <div class="text-surface-900 dark:text-surface-0 font-medium text-2xl mb-2">
        Network Settings Already Exist
      </div>
      <div class="text-muted-color mb-6">
        Network settings have already been configured. You can proceed to the next step.
      </div>
      <Button label="Next" icon="pi pi-arrow-right" iconPos="right" @click="$emit('next')" />
    </div>
    <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-6">
      <!-- Host Settings + Scheduling Settings Column -->
      <div class="col-span-1 flex flex-col gap-1">
        <!-- Host Settings -->
        <div class="bg-surface-50 dark:bg-surface-900 px-3 py-2 rounded-xl flex flex-col gap-1">
          <div class="flex items-center mb-4">
            <span
              class="inline-flex items-center justify-center bg-primary-50 dark:bg-primary-400/10 rounded-full w-8 h-8 mr-3"
            >
              <i class="pi pi-server text-primary text-lg"></i>
            </span>
            <span class="text-surface-900 dark:text-surface-0 font-medium text-lg"
              >Host Settings</span
            >
          </div>
          <div class="flex flex-col gap-3">
            <!-- Host Interface -->
            <span class="p-float-label w-full">
              <label for="host_interface" class="text-surface-600 dark:text-surface-200 font-medium"
                >Host Interface</label
              >
              <Select
                id="host_interface"
                v-model="networkData.host_interface_id"
                :options="hostInterfaces"
                optionLabel="name"
                optionValue="id"
                class="w-full mt-2"
                :class="{ 'p-invalid': submitted && !networkData.host_interface_id }"
              />
            </span>
            <small v-if="submitted && !networkData.host_interface_id" class="p-error block mb-2">
              Host interface is required
            </small>
            <!-- Host Address -->
            <span class="p-float-label w-full">
              <label for="host_address" class="text-surface-600 dark:text-surface-200 font-medium"
                >Host Address</label
              >
              <InputText
                id="host_address"
                v-model.trim="networkData.host_address"
                class="w-full mt-2"
                :class="{ 'p-invalid': submitted && !networkData.host_address }"
              />
            </span>
            <small v-if="submitted && !networkData.host_address" class="p-error block mb-2">
              Host address is required
            </small>
            <!-- Host Subnet Mask -->
            <span class="p-float-label w-full">
              <label
                for="host_subnet_mask"
                class="text-surface-600 dark:text-surface-200 font-medium"
                >Host Subnet Mask</label
              >
              <InputText
                id="host_subnet_mask"
                v-model.trim="networkData.host_subnet_mask"
                class="w-full mt-2"
                :class="{ 'p-invalid': submitted && !networkData.host_subnet_mask }"
              />
            </span>
            <small v-if="submitted && !networkData.host_subnet_mask" class="p-error block mb-2">
              Host subnet mask is required
            </small>
          </div>
        </div>
        <!-- Scheduling Settings (now stacked below Host Settings) -->
        <div class="bg-surface-50 dark:bg-surface-900 px-3 py-2 rounded-xl flex flex-col gap-1 mt-1">
          <div class="flex items-center mb-4">
            <span
              class="inline-flex items-center justify-center bg-primary-50 dark:bg-primary-400/10 rounded-full w-8 h-8 mr-3"
            >
              <i class="pi pi-clock text-primary text-lg"></i>
            </span>
            <span class="text-surface-900 dark:text-surface-0 font-medium text-lg"
              >Scheduling Settings</span
            >
          </div>
          <div class="flex flex-col gap-4">
            <!-- Monitoring Interval -->
            <span class="p-float-label w-full">
              <label for="monitoring_interval" class="text-surface-600 dark:text-surface-200 font-medium"
                >Monitoring Interval</label
              >
              <Dropdown
                id="monitoring_interval"
                v-model="networkData.monitoring_interval"
                :options="monitoringOptions"
                optionLabel="label"
                optionValue="value"
                class="w-full mt-2"
                :class="{ 'p-invalid': submitted && !networkData.monitoring_interval }"
                placeholder="Select Monitoring Interval"
                :showClear="true"
              />
            </span>
            <small v-if="submitted && !networkData.monitoring_interval" class="p-error block mb-2">
              Monitoring interval is required
            </small>
            <!-- Discovery Interval -->
            <span class="p-float-label w-full">
              <label for="discovery_interval" class="text-surface-600 dark:text-surface-200 font-medium"
                >Discovery Interval</label
              >
              <Dropdown
                id="discovery_interval"
                v-model="networkData.discovery_interval"
                :options="discoveryOptions"
                optionLabel="label"
                optionValue="value"
                class="w-full mt-2"
                :class="{ 'p-invalid': submitted && !networkData.discovery_interval }"
                placeholder="Select Discovery Interval"
                :showClear="true"
              />
            </span>
            <small v-if="submitted && !networkData.discovery_interval" class="p-error block mb-2">
              Discovery interval is required
            </small>
          </div>
        </div>
      </div>
      <!-- Management Configurations Section -->
      <div class="col-span-1 flex flex-col mt-2 md:mt-0">
        <div class="bg-surface-50 dark:bg-surface-900 px-3 py-2 rounded-xl flex flex-col gap-2 h-full">
          <div class="flex items-center mb-4">
            <span
              class="inline-flex items-center justify-center bg-primary-50 dark:bg-primary-400/10 rounded-full w-8 h-8 mr-3"
            >
              <i class="pi pi-cog text-primary text-lg"></i>
            </span>
            <span class="text-surface-900 dark:text-surface-0 font-medium text-lg"
              >Management Settings</span
            >
          </div>
          <div class="flex flex-col gap-4">
            <!-- RESTCONF Username -->
            <span class="p-float-label p-input-icon-right w-full">
              <label
                for="restconf_username"
                class="text-surface-600 dark:text-surface-200 font-medium"
                >RESTCONF Username</label
              >
              <InputText
                id="restconf_username"
                v-model.trim="networkData.restconf_username"
                class="w-full mt-2"
                :class="{ 'p-invalid': submitted && !networkData.restconf_username }"
              />
            </span>
            <small v-if="submitted && !networkData.restconf_username" class="p-error block mt-2">
              RESTCONF username is required
            </small>
            <!-- RESTCONF Password -->
            <span class="p-float-label w-full">
              <label
                for="restconf_password"
                class="text-surface-600 dark:text-surface-200 font-medium"
                >RESTCONF Password</label
              >
              <Password
                id="restconf_password"
                v-model="networkData.restconf_password"
                :toggleMask="true"
                :feedback="false"
                class="w-full mt-2"
                :inputClass="{
                  'w-full': true,
                  'p-invalid': submitted && !networkData.restconf_password,
                }"
              />
            </span>
            <!-- Management VRF -->
            <span class="p-float-label w-full">
              <label for="management_vrf" class="text-surface-600 dark:text-surface-200 font-medium"
                >Management VRF Name</label
              >
              <InputText
                id="management_vrf"
                v-model.trim="networkData.management_vrf"
                class="w-full mt-2"
                :class="{ 'p-invalid': submitted && !networkData.management_vrf }"
              />
            </span>
            <small v-if="submitted && !networkData.management_vrf">
              Management VRF is required
            </small>
            <!-- BGP AS -->
            <span class="p-float-label w-full">
              <label for="bgp_as" class="text-surface-600 dark:text-surface-200 font-medium"
                >BGP Autonomous System Number</label
              >
              <Dropdown
                id="bgp_as"
                v-model="networkData.bgp_as"
                :options="bgpAsOptions"
                :filter="true"
                :showClear="true"
                class="w-full mt-2"
                :class="{ 'p-invalid': submitted && !networkData.bgp_as }"
                :virtualScrollerOptions="{ itemSize: 35, style: { height: '350px' } }"
                :filterMatchMode="'contains'"
                :optionLabel="'asLabel'"
                :optionValue="'value'"
                placeholder="Select BGP AS"
              >
                <template #option="slotProps">
                  <span>{{ slotProps.option.value }}</span>
                </template>
              </Dropdown>
            </span>
            <small v-if="submitted && !networkData.bgp_as" class="p-error block mb-2">
              BGP AS number is required
            </small>
            <small v-if="submitted && !networkData.restconf_password" class="p-error block mt-2">
              RESTCONF password is required
            </small>
          </div>
        </div>
      </div>
      <!-- Site Service Settings Section -->
      <div class="col-span-1 flex flex-col mt-2 md:mt-0">
        <div class="bg-surface-50 dark:bg-surface-900 px-3 py-2 rounded-xl flex flex-col gap-2 h-full">
          <div class="flex items-center mb-4">
            <span
              class="inline-flex items-center justify-center bg-primary-50 dark:bg-primary-400/10 rounded-full w-8 h-8 mr-3"
            >
              <i class="pi pi-globe text-primary text-lg"></i>
            </span>
            <span class="text-surface-900 dark:text-surface-0 font-medium text-lg"
              >Site Service Settings</span
            >
          </div>
          <div class="flex flex-col gap-4">
            <span class="p-float-label w-full">
              <label
                for="dhcp_sites_network_address"
                class="text-surface-600 dark:text-surface-200 font-medium"
                >Management Parent Subnet Address</label
              >
              <InputText
                id="dhcp_sites_network_address"
                v-model.trim="networkData.dhcp_sites_network_address"
                class="w-full mt-2"
                :class="{ 'p-invalid': submitted && !networkData.dhcp_sites_network_address }"
              />
            </span>
            <small
              v-if="submitted && !networkData.dhcp_sites_network_address"
              class="p-error block mt-2"
            >
            Management parent subnet address is required
            </small>
            <span class="p-float-label w-full">
              <label
                for="dhcp_sites_network_subnet_mask"
                class="text-surface-600 dark:text-surface-200 font-medium"
                >Management Parent Subnet Mask</label
              >
              <InputText
                id="dhcp_sites_network_subnet_mask"
                v-model.trim="networkData.dhcp_sites_network_subnet_mask"
                class="w-full mt-2"
                :class="{
                  'p-invalid': submitted && !networkData.dhcp_sites_network_subnet_mask,
                }"
              />
            </span>
            <small
              v-if="submitted && !networkData.dhcp_sites_network_subnet_mask"
              class="p-error block mt-2"
            >
              Management parent subnet mask is required
            </small>
            <!-- Link Parent Subnet Address -->
            <span class="p-float-label w-full">
              <label
                for="link_parent_subnet_address"
                class="text-surface-600 dark:text-surface-200 font-medium"
                >Link Parent Subnet Address</label
              >
              <InputText
                id="link_parent_subnet_address"
                v-model.trim="networkData.link_parent_subnet_address"
                class="w-full mt-2"
                :class="{ 'p-invalid': submitted && !networkData.link_parent_subnet_address && submitted }"
              />
            </span>
            <small
              v-if="submitted && !networkData.link_parent_subnet_address"
              class="p-error block mt-2"
            >
              Link parent subnet address is required
            </small>
            <!-- Link Parent Subnet Mask -->
            <span class="p-float-label w-full">
              <label
                for="link_parent_subnet_mask"
                class="text-surface-600 dark:text-surface-200 font-medium"
                >Link Parent Subnet Mask</label
              >
              <InputText
                id="link_parent_subnet_mask"
                v-model.trim="networkData.link_parent_subnet_mask"
                class="w-full mt-2"
                :class="{ 'p-invalid': submitted && !networkData.link_parent_subnet_mask && submitted }"
              />
            </span>
            <small
              v-if="submitted && !networkData.link_parent_subnet_mask"
              class="p-error block mt-2"
            >
              Link parent subnet mask is required
            </small>
          </div>
        </div>
      </div>
      <!-- Navigation Buttons -->
      <div class="col-span-1 md:col-span-3 mt-2">
        <div class="flex items-center justify-between">
          <Button label="Back" icon="pi pi-arrow-left" text @click="$emit('prev')" class="min-w-[6rem]" />
          <Button
            label="Next"
            icon="pi pi-arrow-right"
            iconPos="right"
            @click="handleNext"
            :loading="loading"
            :disabled="loading"
            class="min-w-[6rem]"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import SetupService from '@/service/SetupService'

const toast = useToast()
const emit = defineEmits(['prev', 'next'])

const submitted = ref(false)
const loading = ref(false) // Add loading state
const hostInterfaces = ref([])
const networkSettingsExist = ref(false)

// Generate BGP AS options as objects for better filtering and labeling
const bgpAsOptions = Array.from({ length: 65535 }, (_, i) => ({
  value: i + 1,
  asLabel: String(i + 1),
}))

// Monitoring should be more frequent than discovery
const monitoringOptions = [
  { label: '30 seconds', value: 30 },
  { label: '1 minute', value: 60 },
  { label: '2 minutes', value: 120 },
  { label: '5 minutes', value: 300 },
  { label: '10 minutes', value: 600 },
]
const discoveryOptions = [
  { label: '5 minutes', value: 300 },
  { label: '10 minutes', value: 600 },
  { label: '15 minutes', value: 900 },
  { label: '30 minutes', value: 1800 },
  { label: '60 minutes', value: 3600 },
]

const networkData = reactive({
  management_vrf: '',
  bgp_as: null,
  host_interface_id: null,
  host_address: '',
  host_subnet_mask: '',
  restconf_username: '',
  restconf_password: '',
  dhcp_sites_network_address: '',
  dhcp_sites_network_subnet_mask: '',
  link_parent_subnet_address: '',
  link_parent_subnet_mask: '',
  monitoring_interval: null,
  discovery_interval: null,
})

const handleNext = async () => {
  submitted.value = true

  // Validation check
  if (
    !networkData.management_vrf ||
    !networkData.bgp_as ||
    !networkData.host_interface_id ||
    !networkData.host_address ||
    !networkData.host_subnet_mask ||
    !networkData.restconf_username ||
    !networkData.restconf_password ||
    !networkData.dhcp_sites_network_address ||
    !networkData.dhcp_sites_network_subnet_mask ||
    !networkData.link_parent_subnet_address ||
    !networkData.link_parent_subnet_mask ||
    !networkData.monitoring_interval ||
    !networkData.discovery_interval
  ) {
    toast.add({
      severity: 'error',
      summary: 'Validation Error',
      detail: 'Please fill in all required fields',
      life: 3000,
    })
    return
  }

  loading.value = true // Start loading
  try {
    // Send intervals as seconds (already in seconds in networkData)
    await SetupService.setupNetwork(networkData)
    submitted.value = false
    networkSettingsExist.value = true // Update local state on success
    emit('next')
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: error.message || 'Failed to save network settings',
      life: 3000,
    })
    // If settings already exist, update UI
    if (
      error.response?.status === 400 &&
      error.response?.data?.message?.includes('already exist')
    ) {
      networkSettingsExist.value = true
    }
  } finally {
    loading.value = false // Stop loading
  }
}

onMounted(async () => {
  try {
    const status = await SetupService.checkSetupStatus()
    networkSettingsExist.value = status.has_settings

    if (!networkSettingsExist.value) {
      // Only fetch interfaces if settings don't exist
      const interfaces = await SetupService.getHostInterfaces()
      hostInterfaces.value = interfaces
    }
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to check setup status',
      life: 3000,
    })
  }
})
</script>

<style scoped>
:deep(.p-password-input),
:deep(.p-inputtext),
:deep(.p-inputnumber-input),
:deep(.p-dropdown),
:deep(.p-select) {
  width: 100%;
}
:deep(.p-inputnumber) {
  width: 100%;
}
@media (max-width: 768px) {
  .md\:grid-cols-3 {
    grid-template-columns: 1fr !important;
  }
  .md\:col-span-3 {
    grid-column: span 1 / span 1 !important;
  }
  .md\:mt-0 {
    margin-top: 1rem !important;
  }
}
</style>
