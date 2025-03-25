<template>
  <div class="network-container">
    <!-- Toolbar for zoom and filtering -->
    <div
      class="toolbar p-4 flex items-center justify-between bg-gray-100 dark:bg-gray-800 rounded-lg shadow-md"
    >
      <div class="flex space-x-2">
        <button
          @click="zoomIn"
          class="px-3 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 flex items-center space-x-2"
        >
          <i class="pi pi-search-plus"></i>
          <span>Zoom In</span>
        </button>
        <button
          @click="zoomOut"
          class="px-3 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 flex items-center space-x-2"
        >
          <i class="pi pi-search-minus"></i>
          <span>Zoom Out</span>
        </button>
        <button
          @click="resetView"
          class="px-3 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 flex items-center space-x-2"
        >
          <i class="pi pi-refresh"></i>
          <span>Reset</span>
        </button>
      </div>
    </div>

    <!-- Network Graph -->
    <div class="network-graph-container">
      <v-network-graph
        ref="graph"
        :nodes="graphData.nodes"
        :edges="graphData.edges"
        :layouts="layouts"
        :configs="configs"
        @node-click="onNodeClick"
        @edge-click="onEdgeClick"
        class="h-full w-full"
      />
    </div>

    <!-- Details Dialog -->
    <div
      v-if="selectedElement"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
      <div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full shadow-xl">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-xl font-bold">
            {{ selectedElement.type === 'node' ? 'Node Details' : 'Link Details' }}
          </h2>
          <button @click="closeDetails" class="text-gray-600 hover:text-gray-900">✕</button>
        </div>

        <!-- Node Details -->
        <template v-if="selectedElement.type === 'node'">
          <div v-for="(value, key) in selectedElement.data" :key="key" class="mb-2">
            <span class="font-semibold capitalize">{{ key.replace(/_/g, ' ') }}:</span>
            <span>{{ value }}</span>
          </div>
        </template>

        <!-- Link Details -->
        <template v-else-if="selectedElement.type === 'link'">
          <div v-for="(value, key) in selectedElement.data" :key="key" class="mb-2">
            <span class="font-semibold capitalize">{{ key.replace(/_/g, ' ') }}:</span>
            <span>{{ value }}</span>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
import { VNetworkGraph } from 'v-network-graph'
import 'v-network-graph/lib/style.css'
import { MappingService } from '@/service/MappingService.js'

export default {
  name: 'NetworkMap',
  components: {
    VNetworkGraph,
  },
  data() {
    return {
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
            radius: 25,
            color: (node) => this.getNodeColor(node),
            label: {
              visible: true,
              fontSize: 10,
              fontFamily: 'Arial',
              color: '#000',
            },
          },
        },
        edge: {
          normal: {
            width: 2,
            color: '#777',
            dasharray: '4 2',
            label: {
              visible: true,
              fontSize: 8,
              fontFamily: 'Arial',
              color: '#555',
            },
          },
        },
      },
      selectedElement: null,
      selectedFilter: 'all',
    }
  },
  async created() {
    await this.fetchNetworkData()
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
    getNodeColor(node) {
      switch (node.role) {
        case 'P':
          return '#3498db' // Blue for P routers
        case 'PE':
          return '#e74c3c' // Red for PE routers
        default:
          return '#95a5a6' // Grey for others
      }
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
    applyFilter() {
      // Implement filter logic based on selectedFilter
      const filteredNodes = {}
      const filteredEdges = {}

      Object.entries(this.graphData.nodes).forEach(([id, node]) => {
        if (this.selectedFilter === 'all' || node.role.toLowerCase() === this.selectedFilter) {
          filteredNodes[id] = node
        }
      })

      Object.entries(this.graphData.edges).forEach(([id, edge]) => {
        const sourceNode = this.graphData.nodes[edge.source]
        const targetNode = this.graphData.nodes[edge.target]

        if (
          this.selectedFilter === 'all' ||
          (sourceNode.role.toLowerCase() === this.selectedFilter &&
            targetNode.role.toLowerCase() === this.selectedFilter)
        ) {
          filteredEdges[id] = edge
        }
      })

      // You might want to update this.graphData or use a computed property
      // Depending on your specific requirements
      console.log('Filtered Nodes:', filteredNodes)
      console.log('Filtered Edges:', filteredEdges)
    },
  },
}
</script>

<style scoped>
.network-graph-container {
  height: 600px;
  background-color: #f0f0f0;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
</style>
