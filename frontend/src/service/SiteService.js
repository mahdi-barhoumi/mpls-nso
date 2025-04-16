import axios from 'axios'

const API_URL = 'http://127.0.0.1:8000/api/sites/' // Replace with your actual API endpoint

export default {
  /**
   * Fetch all sites
   * @returns {Promise<Array>} List of sites
   */
  async getSites() {
    try {
      const response = await axios.get(`${API_URL}?expand=true`)
      console.log('Fetched sites:', response.data)
      return response.data
    } catch (error) {
      console.error('Error fetching sites:', error)
      throw error
    }
  },
  //TODO: filter interface that are managment or loopback
  async createSite(site) {
    try {
      const response = await axios.post(API_URL, site)
      return response.data
    } catch (error) {
      console.error('Error creating site:', error)
      throw error
    }
  },

  /**
   * Update an existing site
   * @param {string} id - Site ID
   * @param {Object} site - Updated site data
   * @returns {Promise<Object>} Updated site
   */
  async updateSite(id, site) {
    try {
      const response = await axios.patch(`${API_URL}${id}/`, site)
      return response.data
    } catch (error) {
      console.error('Error updating site:', error)
      throw error
    }
  },

  /**
   * Delete a site
   * @param {string} id - Site ID
   * @returns {Promise<void>}
   */
  async deleteSite(id) {
    try {
      await axios.delete(`${API_URL}${id}/`)
    } catch (error) {
      console.error('Error deleting site:', error)
      throw error
    }
  },
}
