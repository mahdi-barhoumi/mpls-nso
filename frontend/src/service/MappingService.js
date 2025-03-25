import axios from 'axios'

export const MappingService = {
  async fetchNetworkData() {
    try {
      const response = await axios.get('http://127.0.0.1:8000/api/network/map/')
      const data = response.data

      const parsedData = {
        nodes: data.nodes.map((node) => ({
          id: node.id,
          label: node.label,
          type: node.type,
          role: node.role,
          ip: node.ip,
          vrfs: node.vrfs,
          interfaceCounts: node.interface_counts,
        })),
        edges: data.links.map((link) => ({
          id: link.id,
          source: link.source,
          target: link.target,
          label: `${link.sourceInterfaceName} ↔ ${link.targetInterfaceName}`,
          sourceInterface: link.sourceInterface,
          targetInterface: link.targetInterface,
        })),
      }

      return parsedData
    } catch (error) {
      console.error('Error fetching network data:', error)
      throw error
    }
  },
}
