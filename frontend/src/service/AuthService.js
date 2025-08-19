import axios from 'axios'

export default class AuthService {
  async login(username, password) {
    try {
      if (!username?.trim()) {
        throw new Error('Username is required')
      }
      if (!password?.trim()) {
        throw new Error('Password is required')
      }

      const formData = new FormData()
      formData.append('username', username.trim())
      formData.append('password', password.trim())

      const response = await axios.post('http://127.0.0.1:8000/api/auth/login/', formData, {
        withCredentials: true,
      })

      // Store user info in localStorage
      if (response.data.user) {
        localStorage.setItem('user', JSON.stringify(response.data.user))
      }

      return response.data
    } catch (error) {
      // If it's an axios error with response data
      if (error.response?.data) {
        const errorData = error.response.data
        throw {
          message: errorData.error,
          field: errorData.field,
          status: error.response.status,
        }
      }
      // If it's a client-side validation error
      if (error.message) {
        throw {
          message: error.message,
          field: error.message.toLowerCase().includes('username') ? 'username' : 'password',
        }
      }
      // Fallback error
      throw {
        message: 'An unexpected error occurred',
        status: 500,
      }
    }
  }

  async logout() {
    try {
      const response = await axios.delete('http://127.0.0.1:8000/api/auth/logout/', {
        withCredentials: true,
      })

      // Clear user from localStorage
      localStorage.removeItem('user')

      return response.data
    } catch (error) {
      throw {
        message: error.response?.data?.error || 'Failed to log out',
        status: error.response?.status || 500,
      }
    }
  }

  getCurrentUser() {
    try {
      const userStr = localStorage.getItem('user')
      if (userStr) {
        return JSON.parse(userStr)
      }
      return null
    } catch (error) {
      console.error('Error parsing user data:', error)
      localStorage.removeItem('user') // Clear invalid data
      return null
    }
  }

  isAuthenticated() {
    return this.getCurrentUser() !== null
  }
}
