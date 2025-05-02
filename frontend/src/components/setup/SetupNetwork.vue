<template>
  <div
    class="bg-surface-0 dark:bg-surface-900 py-12 px-8 sm:px-20 rounded-[2.5rem] w-full max-w-[80rem] mx-auto"
  >
    <div
      v-if="networkSettingsExist"
      class="flex flex-col items-center justify-center text-center py-12"
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
    <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <!-- Host Network Section -->
      <div class="col-span-1">
        <div class="bg-surface-50 dark:bg-surface-900 p-6 rounded-2xl h-full">
          <div class="flex items-center mb-4">
            <span
              class="inline-flex items-center justify-center bg-primary-50 dark:bg-primary-400/10 rounded-full w-8 h-8 mr-3"
            >
              <i class="pi pi-server text-primary text-lg"></i>
            </span>
            <span class="text-surface-900 dark:text-surface-0 font-medium text-lg"
              >Host Network</span
            >
          </div>
          <div class="flex flex-col gap-2">
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
            <span class="p-float-label w-full">
              <label for="management_vrf" class="text-surface-600 dark:text-surface-200 font-medium"
                >Management VRF</label
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
            <span class="p-float-label w-full">
              <label for="bgp_as" class="text-surface-600 dark:text-surface-200 font-medium"
                >BGP Autonomous System</label
              >
              <InputNumber
                id="bgp_as"
                v-model="networkData.bgp_as"
                :min="1"
                :max="65535"
                class="w-full mt-2"
                :useGrouping="false"
                :class="{ 'p-invalid': submitted && !networkData.bgp_as }"
              />
            </span>
            <small v-if="submitted && !networkData.bgp_as" class="p-error block mb-2">
              BGP AS number is required
            </small>
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
      </div>
      <!-- RESTCONF Section -->
      <div class="col-span-1">
        <div class="bg-surface-50 dark:bg-surface-900 p-6 rounded-2xl h-full">
          <div class="flex items-center mb-4">
            <span
              class="inline-flex items-center justify-center bg-primary-50 dark:bg-primary-400/10 rounded-full w-8 h-8 mr-3"
            >
              <i class="pi pi-lock text-primary text-lg"></i>
            </span>
            <span class="text-surface-900 dark:text-surface-0 font-medium text-lg"
              >RESTCONF Access</span
            >
          </div>
          <div class="flex flex-col gap-2">
            <span class="p-float-label p-input-icon-right w-full">
              <i class="pi pi-user mr-3"></i>
              <label
                for="restconf_username"
                class="text-surface-600 dark:text-surface-200 font-medium"
                >RESTCONF Username</label
              >

              <InputText
                id="restconf_username"
                v-model.trim="networkData.restconf_username"
                class="w-full mt-2 mb-4"
                :class="{ 'p-invalid': submitted && !networkData.restconf_username }"
              />
            </span>
            <small v-if="submitted && !networkData.restconf_username" class="p-error block mt-2">
              RESTCONF username is required
            </small>
            <span class="p-float-label w-full">
              <i class="pi pi-lock mr-3"></i>

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
                class="w-full mt-2 mb-4"
                :inputClass="{
                  'w-full': true,
                  'p-invalid': submitted && !networkData.restconf_password,
                }"
              />
            </span>
            <small v-if="submitted && !networkData.restconf_password" class="p-error block mt-2">
              RESTCONF password is required
            </small>
          </div>
        </div>
      </div>
      <!-- DHCP Configuration Section -->
      <div class="col-span-1">
        <div class="bg-surface-50 dark:bg-surface-900 p-6 rounded-2xl h-full">
          <div class="flex items-center mb-4">
            <span
              class="inline-flex items-center justify-center bg-primary-50 dark:bg-primary-400/10 rounded-full w-8 h-8 mr-3"
            >
              <i class="pi pi-sitemap text-primary text-lg"></i>
            </span>
            <span class="text-surface-900 dark:text-surface-0 font-medium text-lg"
              >DHCP Configuration</span
            >
          </div>
          <div class="flex flex-col gap-2">
            <span class="p-float-label w-full">
              <label
                for="dhcp_sites_network_address"
                class="text-surface-600 dark:text-surface-200 font-medium"
                >Sites Network Address</label
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
              DHCP sites network address is required
            </small>

            <span class="p-float-label w-full">
              <label
                for="dhcp_sites_network_subnet_mask"
                class="text-surface-600 dark:text-surface-200 font-medium"
                >Sites Network Subnet Mask</label
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
              DHCP sites network subnet mask is required
            </small>
          </div>
        </div>
      </div>
      <!-- Navigation Buttons -->
      <div class="col-span-3 mt-8">
        <div class="flex items-center justify-between">
          <Button label="Back" icon="pi pi-arrow-left" text @click="$emit('prev')" />
          <Button label="Next" icon="pi pi-arrow-right" iconPos="right" @click="handleNext" />
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
const hostInterfaces = ref([])
const networkSettingsExist = ref(false)

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
    !networkData.dhcp_sites_network_subnet_mask
  ) {
    toast.add({
      severity: 'error',
      summary: 'Validation Error',
      detail: 'Please fill in all required fields',
      life: 3000,
    })
    return
  }

  try {
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
</style>
