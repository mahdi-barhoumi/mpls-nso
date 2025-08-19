import axios from 'axios'

const API_URL = 'http://127.0.0.1:8000/api/routers/' // Base URL for router-related endpoints

export default {
  /**
   * Fetch all routers
   * @returns {Promise<Array>} List of routers
   */
  async getRouters() {
    try {
      const response = await axios.get(API_URL)
      return response.data
    } catch (error) {
      console.error('Error fetching routers:', error)
      throw error
    }
  },

  /**
   * Fetch all PE routers
   * @returns {Promise<Array>} List of PE routers
   */
  async getPERouters() {
    try {
      const response = await this.getRouters() // Fetch all routers
      return response.filter((router) => router.role === 'Provider Edge')
    } catch (error) {
      console.error('Error fetching PE routers:', error)
      throw error
    }
  },

  /**
   * Fetch all CE routers
   * @returns {Promise<Array>} List of CE routers
   */
  async getCERouters() {
    try {
      const response = await this.getRouters()
      return response.filter((router) => router.role === 'Customer Edge')
    } catch (error) {
      console.error('Error fetching CE routers:', error)
      throw error
    }
  },

  /**
   * Fetch a router by its ID
   * @param {string} routerId - ID of the router to fetch
   * @returns {Promise<Object>} Router details
   */
  async getRouterById(routerId) {
    try {
      const response = await axios.get(`${API_URL}${routerId}/`)
      return response.data
    } catch (error) {
      console.error(`Error fetching router ${routerId}:`, error)
      throw error
    }
  },

  /**
   * Fetch interfaces for a specific router
   * @param {string} routerId - ID of the router
   * @returns {Promise<Array>} List of interfaces for the router
   */
  async getRouterInterfaces(routerId) {
    try {
      const response = await axios.get(`${API_URL}${routerId}/interfaces/`)
      return response.data.interfaces
    } catch (error) {
      console.error(`Error fetching interfaces for router ${routerId}:`, error)
      throw error
    }
  },

  async getConnectedInterfaces(routerId) {
    try {
      const response = await this.getRouterInterfaces(routerId)
      // Only interfaces that are not connected, are physical, and not management
      return response.filter(
        (interfaceObj) =>
          interfaceObj.is_connected === false &&
          interfaceObj.category === 'physical' &&
          interfaceObj.is_management === false,
      )
    } catch (error) {
      console.error(`Error fetching connected interfaces for router ${routerId}:`, error)
      throw error
    }
  },

  /**
   * Fetch VRFs for a specific router
   * @param {string} routerId - ID of the router
   * @returns {Promise<Array>} List of VRFs for the router
   */
  async getRouterVRFs(routerId) {
    try {
      const response = await axios.get(`${API_URL}${routerId}/vrfs/`)
      return response.data.vrfs || []
    } catch (error) {
      console.error(`Error fetching VRFs for router ${routerId}:`, error)
      throw error
    }
  },

  /**
   * Fetch OSPF processes for a specific router
   * @param {string} routerId - ID of the router
   * @returns {Promise<Array>} List of OSPF processes for the router
   */
  async getRouterOSPF(routerId) {
    try {
      const response = await axios.get(`${API_URL}${routerId}/ospf/`)
      return response.data.processes || []
    } catch (error) {
      console.error(`Error fetching OSPF processes for router ${routerId}:`, error)
      throw error
    }
  },

  /**
   * Fetch a single OSPF process (with networks) for a router
   * @param {string} routerId
   * @param {number} processId
   * @returns {Promise<Object>} OSPF process detail
   */
  async getRouterOSPFProcess(routerId, processId) {
    try {
      const response = await axios.get(`${API_URL}${routerId}/ospf/${processId}/`)
      return response.data
    } catch (error) {
      console.error(`Error fetching OSPF process ${processId} for router ${routerId}:`, error)
      throw error
    }
  },
}
