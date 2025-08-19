import axios from 'axios'

const API_URL = 'http://127.0.0.1:8000/api/users/'

export default {
  /**
   * Get user profile
   * @returns {Promise<Object>} User profile data
   */
  async getUserProfile() {
    const response = await axios.get(`${API_URL}profile/`)
    return response.data
  },

  /**
   * Update user profile
   * @param {Object} data Profile update data
   * @returns {Promise<Object>} Updated user profile
   */
  async updateProfile(data) {
    const response = await axios.put(`${API_URL}profile/`, data)
    return response.data
  },
}
