<template>
  <div class="network-container">
    <!-- Toolbar for zoom and filtering -->
    <div class="p-4 flex items-center justify-between surface-card shadow-2 border-round">
      <div class="flex gap-1">
        <Button icon="pi pi-search-plus" class="p-button-secondary" @click="zoomIn" />
        <Button icon="pi pi-search-minus" class="p-button-secondary" @click="zoomOut" />
        <Button label="Reset" icon="pi pi-refresh" class="p-button-secondary" @click="resetView" />
      </div>
    </div>

    <!-- Network Graph -->
    <div class="network-graph-container surface-card shadow-2 border-round mt-3">
      <v-network-graph
        ref="graph"
        :nodes="graphData.nodes"
        :edges="graphData.edges"
        :layouts="layouts"
        :configs="configs"
        @node-click="onNodeClick"
        @edge-click="onEdgeClick"
        class="h-full w-full"
      >
        <!-- Define custom node rendering -->
        <template #override-node="{ nodeId, scale = 1, config, ...slotProps }">
          <!-- <circle :r="config.radius * scale" :fill="`var(--p-primary-color)`" v-bind="slotProps" /> -->
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

    <!-- Details Dialog -->
    <Dialog
      v-if="selectedElement"
      :visible="true"
      :header="selectedElement.type === 'node' ? 'Node Details' : 'Link Details'"
      modal
      class="w-11 sm:w-6"
      @hide="closeDetails"
    >
      <template v-if="selectedElement.type === 'node'">
        <div v-for="(value, key) in selectedElement.data" :key="key" class="mb-2">
          <span class="font-bold capitalize">{{ key.replace(/_/g, ' ') }}:</span>
          <span>{{ value }}</span>
        </div>
      </template>

      <template v-else-if="selectedElement.type === 'link'">
        <div v-for="(value, key) in selectedElement.data" :key="key" class="mb-2">
          <span class="font-bold capitalize">{{ key.replace(/_/g, ' ') }}:</span>
          <span>{{ value }}</span>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script>
import { VNetworkGraph, VEdgeLabel } from 'v-network-graph'
import 'v-network-graph/lib/style.css'
import { MappingService } from '@/service/MappingService.js'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'

export default {
  name: 'NetworkMap',
  components: {
    VNetworkGraph,
    VEdgeLabel,
    Button,
    Dialog,
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
      selectedElement: null,
    }
  },
  created() {
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
  },
  methods: {
    async fetchNetworkData() {
      try {
        const data = await MappingService.fetchNetworkData()

        // Convert arrays to objects for v-network-graph
        const nodesObj = {}
        data.nodes.forEach((node) => {
          nodesObj[node.id] = node
        })

        const edgesObj = {}
        data.edges.forEach((edge) => {
          edgesObj[edge.id] = edge
        })

        this.graphData = {
          nodes: nodesObj,
          edges: edgesObj,
        }

        this.generateCircularLayout()

        // Ensure the graph is centered after data is loaded
        this.$nextTick(() => {
          this.$refs.graph.fitToContents()
        })
      } catch (error) {
        console.error('Error fetching network data:', error)
      }
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
    onNodeClick(event) {
      const nodeId = event.node
      const node = this.graphData.nodes[nodeId]
      if (node) {
        this.selectedElement = {
          type: 'node',
          data: node,
        }
      }
    },
    onEdgeClick(event) {
      const edgeId = event.edge
      const edge = this.graphData.edges[edgeId]
      if (edge) {
        this.selectedElement = {
          type: 'link',
          data: edge,
        }
      }
    },
    closeDetails() {
      this.selectedElement = null
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
  background-color: var(--surface-card);
}
</style>
