import axios from 'axios'

const BASE_URL = 'http://127.0.0.1:8000/api/customers/'

const CustomerService = {
  // Get all customers
  async getCustomers() {
    try {
      const response = await axios.get(BASE_URL)
      return response.data
    } catch (error) {
      console.error('Error fetching customers:', error)
      throw error
    }
  },

  // Get a single customer by ID
  async getCustomer(id) {
    try {
      const response = await axios.get(`${BASE_URL}${id}/`)
      return response.data
    } catch (error) {
      console.error(`Error fetching customer ${id}:`, error)
      throw error
    }
  },

  // Create a new customer
  async createCustomer(customerData) {
    try {
      const response = await axios.post(BASE_URL, customerData)
      return response.data
    } catch (error) {
      console.error('Error creating customer:', error)
      throw error
    }
  },

  // Update an existing customer
  async updateCustomer(id, customerData) {
    try {
      const response = await axios.put(`${BASE_URL}${id}/`, customerData)
      return response.data
    } catch (error) {
      console.error(`Error updating customer ${id}:`, error)
      throw error
    }
  },

  // Delete a customer
  async deleteCustomer(id) {
    try {
      const response = await axios.delete(`${BASE_URL}${id}/`)
      return response.data
    } catch (error) {
      console.error(`Error deleting customer ${id}:`, error)
      throw error
    }
  },
}

export default CustomerService
