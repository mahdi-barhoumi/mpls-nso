import axios from 'axios'

const API_URL = 'http://127.0.0.1:8000/api/logs/'

export default {
  async getLogs(params = {}) {
    try {
      const response = await axios.get(API_URL, { params })
      return response.data
    } catch (error) {
      console.error('Error fetching logs:', error)
      throw error
    }
  },
}
