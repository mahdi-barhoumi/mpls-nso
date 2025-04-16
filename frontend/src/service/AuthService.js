import axios from 'axios'

export default class AuthService {
  async login(username, password) {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)

    const response = await axios.post('http://127.0.0.1:8000/api/auth/login/', formData, {
      withCredentials: true,
    })

    // Store user info in localStorage
    if (response.data.user) {
      localStorage.setItem('user', JSON.stringify(response.data.user))
    }

    return response.data
  }

  async logout() {
    const response = await axios.delete('http://127.0.0.1:8000/api/auth/logout/', {
      withCredentials: true,
    })

    // Clear user from localStorage
    localStorage.removeItem('user')

    return response.data
  }

  getCurrentUser() {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      return JSON.parse(userStr)
    }
    return null
  }

  isAuthenticated() {
    return this.getCurrentUser() !== null
  }
}
