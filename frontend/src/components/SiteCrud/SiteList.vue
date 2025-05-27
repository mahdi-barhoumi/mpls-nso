<template>
  <div>
    <div v-if="loading" style="padding: 20px; text-align: center">Loading sites...</div>

    <div v-else-if="sites.length === 0" style="padding: 20px; text-align: center; color: #666">
      No sites found. Create your first site above.
    </div>

    <div v-else>
      <table style="width: 100%; border-collapse: collapse; margin-top: 20px">
        <thead>
          <tr style="background-color: #f5f5f5">
            <th style="border: 1px solid #ccc; padding: 10px; text-align: left">Name</th>
            <th style="border: 1px solid #ccc; padding: 10px; text-align: left">Location</th>
            <th style="border: 1px solid #ccc; padding: 10px; text-align: left">Customer</th>
            <th style="border: 1px solid #ccc; padding: 10px; text-align: left">
              Provider Interface
            </th>
            <th style="border: 1px solid #ccc; padding: 10px; text-align: left">Customer Edge</th>
            <th style="border: 1px solid #ccc; padding: 10px; text-align: left">
              Management Subnet
            </th>
            <th style="border: 1px solid #ccc; padding: 10px; text-align: left">Link Subnet</th>
            <th style="border: 1px solid #ccc; padding: 10px; text-align: left">Status</th>
            <th style="border: 1px solid #ccc; padding: 10px; text-align: left">Routing</th>
            <th style="border: 1px solid #ccc; padding: 10px; text-align: left">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="site in sites" :key="site.id">
            <td style="border: 1px solid #ccc; padding: 10px">{{ site.name }}</td>
            <td style="border: 1px solid #ccc; padding: 10px">{{ site.location || 'N/A' }}</td>
            <td style="border: 1px solid #ccc; padding: 10px">
              {{ site.customer?.name || 'N/A' }}
            </td>
            <td style="border: 1px solid #ccc; padding: 10px">
              {{ site.assigned_interface?.router?.hostname || 'N/A' }} via
              {{ site.assigned_interface?.name || 'N/A' }}
            </td>
            <td style="border: 1px solid #ccc; padding: 10px">
              {{ site.CE_router?.hostname || 'N/A' }}
            </td>
            <td style="border: 1px solid #ccc; padding: 10px">{{ site.dhcp_scope || 'N/A' }}</td>
            <td style="border: 1px solid #ccc; padding: 10px">{{ site.link_network || 'N/A' }}</td>
            <td style="border: 1px solid #ccc; padding: 10px">
              <span :style="{ color: getStatusColor(site.status) }">
                {{ getStatusText(site.status) }}
              </span>
            </td>
            <td style="border: 1px solid #ccc; padding: 10px">
              <span :style="{ color: site.has_routing ? 'green' : 'red' }">
                {{ site.has_routing ? 'Enabled' : 'Disabled' }}
              </span>
            </td>
            <td style="border: 1px solid #ccc; padding: 10px">
              <button @click="handleEdit(site)" style="padding: 5px 10px; margin-right: 5px">
                Edit
              </button>
              <button
                @click="handleDelete(site)"
                style="
                  padding: 5px 10px;
                  margin-right: 5px;
                  background-color: #dc3545;
                  color: white;
                "
                :disabled="deleting === site.id"
              >
                {{ deleting === site.id ? 'Deleting...' : 'Delete' }}
              </button>
              <button
                v-if="site.has_routing"
                @click="handleDisableRouting(site)"
                style="padding: 5px 10px; background-color: #fd7e14; color: white"
                :disabled="routingAction === site.id"
              >
                {{ routingAction === site.id ? 'Processing...' : 'Disable Routing' }}
              </button>
              <button
                v-else
                @click="handleEnableRouting(site)"
                :style="{
                  padding: '5px 10px',
                  backgroundColor: isStatusActive(site.status) ? '#28a745' : '#6c757d',
                  color: 'white',
                  opacity: isStatusActive(site.status) ? '1' : '0.6',
                  cursor: isStatusActive(site.status) ? 'pointer' : 'not-allowed',
                }"
                :disabled="routingAction === site.id || !isStatusActive(site.status)"
              >
                {{ routingAction === site.id ? 'Processing...' : 'Enable Routing' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  sites: Array,
  loading: Boolean,
  deleting: Number,
  routingAction: Number,
})

const emit = defineEmits(['edit', 'delete', 'enable-routing', 'disable-routing'])

// Helper functions for status handling
const isStatusActive = (status) => {
  if (typeof status === 'boolean') {
    return status === true
  }
  return status === 'active'
}

const getStatusText = (status) => {
  if (typeof status === 'boolean') {
    return status ? 'Active' : 'Inactive'
  }
  if (status === 'active') return 'Active'
  if (status === 'inactive') return 'Inactive'
  return status || 'Offline'
}

const getStatusColor = (status) => {
  if (isStatusActive(status)) {
    return 'green'
  }
  if (typeof status === 'boolean' && status === false) {
    return 'red'
  }
  if (status === 'inactive') {
    return 'red'
  }
  return 'orange'
}

const handleEdit = (site) => {
  emit('edit', site)
}

const handleDelete = (site) => {
  emit('delete', site)
}

const handleEnableRouting = (site) => {
  emit('enable-routing', site)
}

const handleDisableRouting = (site) => {
  emit('disable-routing', site)
}
</script>
