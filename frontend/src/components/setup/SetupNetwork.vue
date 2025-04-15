<template>
  <div
    class="bg-surface-0 dark:bg-surface-900 py-9 px-8 sm:px-20 rounded-[2.5rem] w-full max-w-[48rem] mx-auto"
  >
    <div class="grid gap-8">
      <!-- Host Network Section -->
      <div class="col-span-12 md:col-span-6">
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
              <Dropdown
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
          </div>
        </div>
      </div>
      <!-- RESTCONF Section -->
      <div class="col-span-12 md:col-span-6">
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
      <div class="col-span-12">
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
          <div class="flex flex-col gap-2 md:flex-row md:gap-8">
            <div class="flex-1 flex flex-col gap-2">
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
            </div>
            <div class="flex-1 flex flex-col gap-2">
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
            <div class="flex-1 flex flex-col gap-2">
              <span class="p-float-label w-full">
                <label
                  for="dhcp_lease_time"
                  class="text-surface-600 dark:text-surface-200 font-medium"
                  >DHCP Lease Time</label
                >
                <InputNumber
                  id="dhcp_lease_time"
                  v-model="networkData.dhcp_lease_time"
                  :min="86400"
                  suffix=" seconds"
                  :useGrouping="false"
                  class="w-full mt-2"
                  :class="{ 'p-invalid': submitted && !networkData.dhcp_lease_time }"
                />
              </span>
              <small v-if="submitted && !networkData.dhcp_lease_time" class="p-error block mt-2">
                DHCP lease time is required (minimum 86400 seconds)
              </small>
            </div>
          </div>
        </div>
      </div>
      <!-- Navigation Buttons -->
      <div class="col-span-12">
        <div class="flex items-center justify-between mt-8">
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

const networkData = reactive({
  management_vrf: '',
  bgp_as: null,
  host_interface_id: null,
  restconf_username: '',
  restconf_password: '',
  dhcp_sites_network_address: '',
  dhcp_sites_network_subnet_mask: '',
  dhcp_lease_time: 86400,
})

const handleNext = async () => {
  submitted.value = true

  if (
    !networkData.management_vrf ||
    !networkData.bgp_as ||
    !networkData.host_interface_id ||
    !networkData.restconf_username ||
    !networkData.restconf_password ||
    !networkData.dhcp_sites_network_address ||
    !networkData.dhcp_sites_network_subnet_mask ||
    !networkData.dhcp_lease_time
  ) {
    return
  }

  try {
    await SetupService.setupNetwork(networkData)
    submitted.value = false
    emit('next')
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: error.response?.data?.message || 'Failed to save network settings',
      life: 3000,
    })
  }
}

onMounted(async () => {
  try {
    const interfaces = await SetupService.getHostInterfaces()
    hostInterfaces.value = interfaces
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to fetch host interfaces',
      life: 3000,
    })
  }
})
</script>

<style scoped>
:deep(.p-password-input),
:deep(.p-inputtext),
:deep(.p-inputnumber-input),
:deep(.p-dropdown) {
  width: 100%;
}
:deep(.p-inputnumber) {
  width: 100%;
}
</style>
