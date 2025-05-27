import axios from 'axios'

const API_URL = 'http://127.0.0.1:8000/api/sites/'

export default {
  /**
   * Fetch all sites
   * @returns {Promise<Array>} List of sites
   */
  async getSites() {
    try {
      const response = await axios.get(`${API_URL}?expand=true`)
      return response.data
    } catch (error) {
      console.error('Error fetching sites:', error)
      throw error
    }
  },
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

  /**
   * Enable routing for a site
   * @param {number} siteId - Site ID
   * @returns {Promise<Object>} Response data
   */
  async enableRouting(siteId) {
    try {
      const response = await axios.post(`http://127.0.0.1:8000/api/sites/${siteId}/enable-routing/`)
      return response.data
    } catch (error) {
      console.error('Error enabling routing for site:', error)
      throw error
    }
  },

  /**
   * Disable routing for a site
   * @param {number} siteId - Site ID
   * @returns {Promise<Object>} Response data
   */
  async disableRouting(siteId) {
    try {
      const response = await axios.delete(
        `http://127.0.0.1:8000/api/sites/${siteId}/enable-routing/`,
      )
      return response.data
    } catch (error) {
      console.error('Error disabling routing for site:', error)
      throw error
    }
  },
}
