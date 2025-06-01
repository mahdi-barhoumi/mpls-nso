<template>
  <div class="card h-full">
    <div class="flex justify-between mb-2">
      <div>
        <h5 class="text-lg m-1">Network Topology</h5>
        <div class="flex gap-2">
          <div class="flex items-center gap-2">
            <div
              class="flex items-center justify-center bg-blue-100 dark:bg-blue-400/10 rounded-border"
              style="width: 1.5rem; height: 1.5rem"
            >
              <img src="/demo/images/routers/router_black.svg" class="w-4 h-4" alt="P Router" />
            </div>
            <span class="text-sm">P Router</span>
          </div>
          <div class="flex items-center gap-2">
            <div
              class="flex items-center justify-center bg-orange-100 dark:bg-orange-400/10 rounded-border"
              style="width: 1.5rem; height: 1.5rem"
            >
              <img src="/demo/images/routers/router_blue.svg" class="w-4 h-4" alt="PE Router" />
            </div>
            <span class="text-sm">PE Router</span>
          </div>
          <div class="flex items-center gap-2">
            <div
              class="flex items-center justify-center bg-green-100 dark:bg-green-400/10 rounded-border"
              style="width: 1.5rem; height: 1.5rem"
            >
              <img
                src="/demo/images/routers/router-in-building.svg"
                class="w-4 h-4"
                alt="CE Router"
              />
            </div>
            <span class="text-sm">CE Router</span>
          </div>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <div
          class="flex items-center justify-center bg-purple-100 dark:bg-purple-400/10 rounded-border p-2"
        >
          <Button icon="pi pi-search-plus" class="p-button-text p-button-rounded" @click="zoomIn" />
        </div>
        <div
          class="flex items-center justify-center bg-cyan-100 dark:bg-cyan-400/10 rounded-border p-2"
        >
          <Button
            icon="pi pi-search-minus"
            class="p-button-text p-button-rounded"
            @click="zoomOut"
          />
        </div>
        <div
          class="flex items-center justify-center bg-orange-100 dark:bg-orange-400/10 rounded-border p-2"
        >
          <Button icon="pi pi-refresh" class="p-button-text p-button-rounded" @click="resetView" />
        </div>
      </div>
    </div>

    <div class="network-graph-container border-round mt-3">
      <v-network-graph
        ref="graph"
        :nodes="graphData.nodes"
        :edges="graphData.edges"
        :layouts="layouts"
        :configs="configs"
        :event-handlers="eventHandlers"
        @mouseup="saveLayout"
        @layout-updated="onLayoutUpdated"
        class="h-full w-full"
      >
        <!-- Custom node rendering -->
        <template #override-node="{ nodeId, scale = 1, config, ...slotProps }">
          <g>
            <image
              :xlink:href="getNodeIcon(nodeId)"
              :x="-(selectedNodeId === nodeId ? (config.radius - 8) * 1.15 * scale : (config.radius - 8) * scale)"
              :y="-(selectedNodeId === nodeId ? (config.radius - 8) * 1.15 * scale : (config.radius - 8) * scale)"
              :width="(selectedNodeId === nodeId ? (config.radius - 8) * 2 * 1.15 * scale : (config.radius - 8) * 2 * scale)"
              :height="(selectedNodeId === nodeId ? (config.radius - 8) * 2 * 1.15 * scale : (config.radius - 8) * 2 * scale)"
              :style="selectedNodeId === nodeId ? 'filter: brightness(0.8);' : ''"
            />
            <text
              :x="0"
              :y="(config.radius + 12) * scale"
              :font-size="(selectedNodeId === nodeId ? 15 : 13) * scale"
              font-weight="500"
              text-anchor="middle"
              dominant-baseline="central"
              :fill="getLabelColor()"
              style="letter-spacing:0.5px;"
            >
              {{ getNodeName(nodeId) }}
            </text>
          </g>
        </template>

        <!-- Custom edge labels -->
        <template #edge-label="{ edge, scale = 1, ...slotProps }">
          <v-edge-label
            :text="edge.subnet"
            align="center"
            :vertical-align="(edge.sourceInterfaceType === 'logical' || edge.targetInterfaceType === 'logical') ? 'below' : 'above'"
            v-bind="slotProps"
            :fill="getEdgeLabelColor()"
            :font-size="10 * (scale || 1)"
            font-weight="400"
            style="letter-spacing:0.2px;"
          />
          <v-edge-label
            :text="abbreviateIface(edge.sourceInterfaceName)"
            align="source"
            :vertical-align="(edge.sourceInterfaceType === 'logical' || edge.targetInterfaceType === 'logical') ? 'below' : 'above'"
            v-bind="slotProps"
            :fill="getIfaceLabelColor()"
            :font-size="9 * (scale || 1)"
            font-weight="400"
            style="letter-spacing:0.2px;"
          />
          <v-edge-label
            :text="abbreviateIface(edge.targetInterfaceName)"
            align="target"
            :vertical-align="(edge.sourceInterfaceType === 'logical' || edge.targetInterfaceType === 'logical') ? 'below' : 'above'"
            v-bind="slotProps"
            :font-size="9 * (scale || 1)"
            font-weight="400"
            :fill="getIfaceLabelColor()"
            style="letter-spacing:0.2px;"
          />
        </template>
      </v-network-graph>
    </div>
  </div>
</template>

<script>
import { VNetworkGraph, VEdgeLabel } from 'v-network-graph'
import 'v-network-graph/lib/style.css'
import { MappingService } from '@/service/MappingService.js'
import Button from 'primevue/button'

const STORAGE_KEYS = {
  NODES: 'network-graph-nodes',
  LAYOUTS: 'network-graph-layouts',
  FETCHED_NODES: 'network-graph-fetched-nodes',
}

export default {
  name: 'NetworkMap',
  components: {
    VNetworkGraph,
    VEdgeLabel,
    Button,
  },
  data() {
    return {
      pollingInterval: null,
      graphData: {
        nodes: {},
        edges: {},
      },
      layouts: {
        nodes: {},
      },
      fetchedNodeIds: new Set(),
      selectedNodeId: null, // Track selected node
      configs: {
        view: {
          panEnabled: true,
          zoomEnabled: true,
          minZoom: 0.1,
          maxZoom: 5,
          initialZoom: 1,
          fitContentMargin: 50,
        },
        node: {
          normal: {
            type: 'circle',
            radius: 30,
            color: '#ffffff', // Default background color for nodes
            label: {
              visible: true,
              fontSize: 10,
              fontFamily: 'var(--font-family)',
              color: '#000',
            },
          },
          draggable: true, // Ensure nodes are draggable
        },
        edge: {
          normal: {
            width: 2,
            color: 'var(--p-blue-400)',
            dasharray: '4 2',
            label: {
              visible: false, // Disable default edge labels
            },
          },
        },
      },

      saveDebounce: null,
      eventHandlers: {
        'node:click': ({ node }) => {
          const nodeData = this.graphData.nodes[node]
          if (nodeData) {
            this.selectedNodeId = node // Set selected node
            this.$emit('node-selected', node)
          }
        },
        'edge:click': ({ edge }) => {
          // Optionally handle edge clicks if needed
        },
      },
    }
  },
  created() {
    // Load persisted data
    this.loadPersistedData()

    // Initial fetch
    this.fetchNetworkData()

    // Set up polling every 30 seconds
    this.pollingInterval = setInterval(() => {
      this.fetchNetworkData()
    }, 30000)
  },
  beforeUnmount() {
    // Clean up polling interval when component is destroyed
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval)
    }

    // Clear any pending debounce
    if (this.saveDebounce) {
      clearTimeout(this.saveDebounce)
    }
  },
  methods: {
    loadPersistedData() {
      try {
        // Load previously fetched node IDs
        const fetchedNodesJson = localStorage.getItem(STORAGE_KEYS.FETCHED_NODES)
        if (fetchedNodesJson) {
          this.fetchedNodeIds = new Set(JSON.parse(fetchedNodesJson))
        }

        // Load persisted layouts
        const layoutsJson = localStorage.getItem(STORAGE_KEYS.LAYOUTS)
        if (layoutsJson) {
          this.layouts.nodes = JSON.parse(layoutsJson)
        }

        // Load persisted nodes
        const nodesJson = localStorage.getItem(STORAGE_KEYS.NODES)
        if (nodesJson) {
          this.graphData.nodes = JSON.parse(nodesJson)
        }
      } catch (error) {
        console.error('Error loading persisted data:', error)
        // If there's an error loading persisted data, fallback to default behavior
        this.fetchedNodeIds = new Set()
        this.layouts = { nodes: {} }
      }
    },

    persistData() {
      try {
        // Save fetched node IDs
        localStorage.setItem(STORAGE_KEYS.FETCHED_NODES, JSON.stringify([...this.fetchedNodeIds]))

        // Save layouts
        localStorage.setItem(STORAGE_KEYS.LAYOUTS, JSON.stringify(this.layouts.nodes))

        // Save nodes
        localStorage.setItem(STORAGE_KEYS.NODES, JSON.stringify(this.graphData.nodes))
      } catch (error) {
        console.error('Error persisting data:', error)
      }
    },

    // Use both event handlers to ensure we catch the drag event regardless of library version
    onLayoutUpdated(event) {
      // Debounce the save operation to avoid excessive writes
      if (this.saveDebounce) {
        clearTimeout(this.saveDebounce)
      }

      this.saveDebounce = setTimeout(() => {
        this.persistData()
      }, 500) // Save after 500ms of inactivity
    },

    async fetchNetworkData() {
      try {
        const data = await MappingService.fetchNetworkData()

        // Get current node IDs from backend
        const currentNodeIds = new Set(data.nodes.map((node) => node.id))

        // Create new nodes object while preserving existing node data
        const nodesObj = {}

        // First, add all existing nodes that are still present in backend
        Object.entries(this.graphData.nodes).forEach(([id, node]) => {
          if (currentNodeIds.has(Number(id))) {
            nodesObj[id] = node
          }
        })

        // Then add or update nodes from backend
        data.nodes.forEach((node) => {
          if (nodesObj[node.id]) {
            // Update existing node data while preserving other properties
            nodesObj[node.id] = { ...nodesObj[node.id], ...node }
          } else {
            // Add new node
            nodesObj[node.id] = node
          }
        })

        // Update edges
        const edgesObj = {}
        data.edges.forEach((edge) => {
          edgesObj[edge.id] = edge
        })

        // Update graph data
        this.graphData = {
          nodes: nodesObj,
          edges: edgesObj,
        }

        // Generate layout only for new nodes
        const newNodes = data.nodes
          .filter((node) => !this.layouts.nodes[node.id])
          .map((node) => node.id)

        if (newNodes.length > 0) {
          this.generateLayoutForNewNodes(newNodes)
        }

        // Persist the updated data
        this.persistData()

        // Only fit to contents if there are new nodes
        if (newNodes.length > 0) {
          this.$nextTick(() => {
            this.$refs.graph.fitToContents()
          })
        }
      } catch (error) {
        console.error('Error fetching network data:', error)
      }
    },

    generateLayoutForNewNodes(nodeIds) {
      // Only generate layout for nodes that don't already have positions
      const newNodeIds = nodeIds.filter((id) => !this.layouts.nodes[id])

      if (newNodeIds.length === 0) return

      const centerX = 500
      const centerY = 300
      const radius = 250

      // Keep existing layouts and only add new ones
      const updatedLayouts = { ...this.layouts.nodes }

      newNodeIds.forEach((id, index) => {
        const angle = (index / newNodeIds.length) * 2 * Math.PI
        updatedLayouts[id] = {
          x: centerX + radius * Math.cos(angle),
          y: centerY + radius * Math.sin(angle),
        }
      })

      this.layouts = { nodes: updatedLayouts }
    },

    generateCircularLayout() {
      const nodeIds = Object.keys(this.graphData.nodes)
      const centerX = 500
      const centerY = 300
      const radius = 250

      const layouts = {}
      nodeIds.forEach((id, index) => {
        const angle = (index / nodeIds.length) * 2 * Math.PI
        layouts[id] = {
          x: centerX + radius * Math.cos(angle),
          y: centerY + radius * Math.sin(angle),
        }
      })

      this.layouts = { nodes: layouts }
      this.persistData()
    },

    saveLayout() {
      this.persistData()
      // Show a small success notification or toast here
    },

    getNodeIcon(nodeId) {
      const node = this.graphData.nodes[nodeId]
      if (node.role === 'P') {
        return '/demo/images/routers/router_black.svg' // Black router image for P routers
      } else if (node.role === 'PE') {
        return '/demo/images/routers/router_blue.svg' // Blue router image for PE routers
      }
      return '/demo/images/routers/router-in-building.svg'
    },

    getNodeName(nodeId) {
      const node = this.graphData.nodes[nodeId]
      return node.label
    },

    getLabelColor() {
      // Theme-aware: dark text on light, light text on dark
      return document.documentElement.className.includes('dark') ? '#e5e7eb' : '#222';
    },

    getEdgeLabelColor() {
      // Slightly muted, theme-aware
      return document.documentElement.className.includes('dark') ? '#cbd5e1' : '#374151';
    },

    getIfaceLabelColor() {
      // Even more muted, theme-aware
      return document.documentElement.className.includes('dark') ? '#94a3b8' : '#64748b';
    },

    abbreviateIface(name) {
      if (!name) return ''
      return name
        .replace(/^GigabitEthernet/, 'Gi')
        .replace(/^FastEthernet/, 'Fa')
        .replace(/^TenGigabitEthernet/, 'Te')
        .replace(/^Ethernet/, 'Eth')
        .replace(/^Port-channel/, 'Po')
        .replace(/^Loopback/, 'Lo')
        .replace(/^Serial/, 'Se')
    },

    zoomIn() {
      this.$refs.graph.zoomIn()
    },

    zoomOut() {
      this.$refs.graph.zoomOut()
    },

    resetView() {
      this.$refs.graph.fitToContents()
    },
  },
}
</script>

<style scoped>
.network-graph-container {
  height: 600px;
  background-color: var(--surface-ground);
  border: 1px solid var(--surface-border);
}

/* Subtle, visible edge lines */
:deep(.v-network-graph-edge-path) {
  stroke: #a3a3a3 !important;
  stroke-width: 2.5px !important;
  opacity: 0.85;
}

.p-button.p-button-text {
  color: var(--primary-color);
  padding: 0;
}

.p-button.p-button-text:hover {
  background: transparent;
  color: var(--primary-600);
}
</style>
