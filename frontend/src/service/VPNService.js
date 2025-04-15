import axios from 'axios'

const API_URL = 'http://127.0.0.1:8000/api/vpns/'

export default {
  async getVPNs() {
    try {
      const response = await axios.get(`${API_URL}?expand=sites`)
      return response.data
    } catch (error) {
      console.error('Error fetching VPNs:', error)
      throw error
    }
  },
  async getVPN(id) {
    try {
      const response = await axios.get(`${API_URL}${id}/`)
      return response.data
    } catch (error) {
      console.error('Error fetching VPN:', error)
      throw error
    }
  },
  async createVPN(vpnData) {
    try {
      const response = await axios.post(API_URL, vpnData)
      return response.data
    } catch (error) {
      console.error('Error creating VPN:', error)
      throw error
    }
  },

  async deleteVPN(id) {
    try {
      await axios.delete(`${API_URL}${id}/`)
      return true
    } catch (error) {
      console.error('Error deleting VPN:', error)
      throw error
    }
  },

  async addSiteToVPN(vpnId, siteId) {
    try {
      const response = await axios.post(`${API_URL}${vpnId}/sites/`, {
        site_id: siteId,
      })
      return response.data
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Failed to add site to VPN'
      console.error('Error adding site to VPN:', error)
      throw errorMessage
    }
  },

  async updateVPN(id, vpnData) {
    try {
      const response = await axios.patch(`${API_URL}${id}/`, vpnData)
      return response.data
    } catch (error) {
      console.error('Error updating VPN:', error)
      if (error.response?.status === 405) {
        throw new Error('VPN update operation not supported')
      }
      throw error.response?.data?.error || error.message
    }
  },

  async removeSiteFromVPN(vpnId, siteId) {
    try {
      await axios.delete(`${API_URL}${vpnId}/sites/${siteId}/`)
      return true
    } catch (error) {
      console.error('Error removing site from VPN:', error)
      throw error
    }
  },
}
