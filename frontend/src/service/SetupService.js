import axios from 'axios'

const API_URL = 'http://127.0.0.1:8000/api/setup/'

export default {
  async checkSetupStatus() {
    try {
      const response = await axios.get(`${API_URL}status/`)
      return response.data
    } catch (error) {
      console.error('Error checking setup status:', error)
      throw error
    }
  },

  async setupAdmin(adminData) {
    try {
      const response = await axios.post(`${API_URL}admin/`, adminData)
      return response.data
    } catch (error) {
      console.error('Error setting up admin:', error)
      throw error
    }
  },

  async setupSettings(settingsData) {
    try {
      const response = await axios.post(`${API_URL}settings/`, settingsData)
      return response.data
    } catch (error) {
      console.error('Error setting up settings:', error)
      throw error
    }
  },

  async getHostInterfaces() {
    try {
      const response = await axios.get('http://127.0.0.1:8000/api/utils/host-interfaces/')
      return response.data
    } catch (error) {
      console.error('Error fetching host interfaces:', error)
      throw error
    }
  },
}
