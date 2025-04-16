<template>

  <div class="col-span-12">
    <div class="card mb-3">
      <div class="flex justify-between mb-4">
        <div>
          <span class="block text-muted-color font-medium mb-2">Network Topology</span>
          <div class="flex gap-2">
            <div class="flex items-center gap-2">
              <div
                class="flex items-center justify-center bg-blue-100 dark:bg-blue-400/10 rounded-border"
                style="width: 1.5rem; height: 1.5rem"
              >
                <i class="pi pi-circle-fill text-blue-500 text-xs"></i>
              </div>
              <span class="text-sm">P Router</span>
            </div>
            <div class="flex items-center gap-2">
              <div
                class="flex items-center justify-center bg-orange-100 dark:bg-orange-400/10 rounded-border"
                style="width: 1.5rem; height: 1.5rem"
              >
                <i class="pi pi-circle-fill text-orange-500 text-xs"></i>
              </div>
              <span class="text-sm">PE Router</span>
            </div>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <div
            class="flex items-center justify-center bg-purple-100 dark:bg-purple-400/10 rounded-border p-2"
          >
            <Button
              icon="pi pi-search-plus"
              class="p-button-text p-button-rounded"
              @click="zoomIn"
            />
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
            <Button
              icon="pi pi-refresh"
              class="p-button-text p-button-rounded"
              @click="resetView"
            />
          </div>
          <div
            class="flex items-center justify-center bg-blue-100 dark:bg-blue-400/10 rounded-border p-2"
          >
            <Button icon="pi pi-save" class="p-button-text p-button-rounded" @click="saveLayout" />
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
          <!-- Define custom node rendering -->
          <template #override-node="{ nodeId, scale = 1, config, ...slotProps }">
            <text
              :x="0"
              :y="(config.radius + 10) * scale"
              :font-size="12 * scale"
              text-anchor="middle"
              dominant-baseline="central"
              fill="var(--p-blue-600)"
            >
              {{ getNodeName(nodeId) }}
            </text>
            <image
              :xlink:href="getNodeIcon(nodeId)"
              :x="-(config.radius - 8) * scale"
              :y="-(config.radius - 8) * scale"
              :width="(config.radius - 8) * 2 * scale"
              :height="(config.radius - 8) * 2 * scale"
            />
          </template>

          <!-- Define custom edge labels -->
          <template #edge-label="{ edge, scale = 1, ...slotProps }">
            <v-edge-label
              v-if="
                edge.sourceInterfaceType === 'physical' && edge.targetInterfaceType === 'physical'
              "
              :text="edge.subnet"
              align="center"
              vertical-align="above"
              v-bind="slotProps"
              fill="var(--p-primary-500)"
              :font-size="10 * (scale || 1)"
            />
            <v-edge-label
              v-if="
                edge.sourceInterfaceType === 'physical' && edge.targetInterfaceType === 'physical'
              "
              :text="edge.sourceInterfaceName"
              align="source"
              vertical-align="above"
              v-bind="slotProps"
              fill="var(--text-color)"
              :font-size="10 * (scale || 1)"
            />
            <v-edge-label
              v-if="
                edge.sourceInterfaceType === 'physical' && edge.targetInterfaceType === 'physical'
              "
              :text="edge.targetInterfaceName"
              align="target"
              vertical-align="above"
              v-bind="slotProps"
              :font-size="10 * (scale || 1)"
              fill="var(--text-color)"
            />
          </template>
        </v-network-graph>
      </div>
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
            this.$emit('node-selected', node) // Just emit the node ID
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
      // This is called whenever the layout is changed
      console.log('Layout updated:', event)

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

        // Convert arrays to objects for v-network-graph, maintaining previously fetched nodes
        const nodesObj = { ...this.graphData.nodes }
        data.nodes.forEach((node) => {
          nodesObj[node.id] = node
          this.fetchedNodeIds.add(node.id)
        })

        const edgesObj = {}
        data.edges.forEach((edge) => {
          edgesObj[edge.id] = edge
        })

        this.graphData = {
          nodes: nodesObj,
          edges: edgesObj,
        }

        // Only generate circular layout for nodes that don't have saved positions
        this.generateLayoutForNewNodes(Object.keys(nodesObj))

        // Persist the updated data
        this.persistData()

        // Ensure the graph is centered after data is loaded
        this.$nextTick(() => {
          this.$refs.graph.fitToContents()
        })
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

.p-button.p-button-text {
  color: var(--primary-color);
  padding: 0;
}

.p-button.p-button-text:hover {
  background: transparent;
  color: var(--primary-600);
}
</style>
