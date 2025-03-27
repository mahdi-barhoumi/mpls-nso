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
          sourceInterfaceName: abbreviateInterfaceName(link.sourceInterfaceName),
          targetInterfaceName: abbreviateInterfaceName(link.targetInterfaceName),
          sourceInterfaceIp: link.sourceInterfaceDetails.ip_address,
          sourceInterfaceMask: link.sourceInterfaceDetails.subnet_mask,
          subnet: calculateSubnet(
            link.sourceInterfaceDetails.ip_address,
            link.sourceInterfaceDetails.subnet_mask,
          ),
        })),
      }

      return parsedData
    } catch (error) {
      console.error('Error fetching network data:', error)
      throw error
    }
  },
}
// Utility function to calculate the subnet
function calculateSubnet(ipAddress, subnetMask) {
  if (!ipAddress || !subnetMask) return null

  const ipParts = ipAddress.split('.').map(Number)
  const maskParts = subnetMask.split('.').map(Number)

  if (ipParts.length !== 4 || maskParts.length !== 4) return null

  // Calculate the subnet address
  const subnetParts = ipParts.map((part, index) => part & maskParts[index])
  const subnetAddress = subnetParts.join('.')

  // Calculate the subnet length (number of bits set to 1 in the mask)
  const subnetLength =
    maskParts
      .map((part) => part.toString(2).padStart(8, '0')) // Convert each octet to binary
      .join('') // Combine all binary strings
      .split('1').length - 1 // Count the number of '1's

  return `${subnetAddress}/${subnetLength}` // Combine subnet address and length
}
// Utility function to abbreviate interface names
function abbreviateInterfaceName(interfaceName) {
  if (!interfaceName) return null

  // Extract the first two letters and append any trailing numbers or symbols
  const match = interfaceName.match(/^([a-zA-Z]{2})[a-zA-Z]*([\d./]*)/)
  if (match) {
    const [, prefix, suffix] = match
    return `${prefix}${suffix}`
  }

  return interfaceName // Return the original name if no match
}
