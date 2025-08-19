import axios from 'axios'

const API_URL = 'http://127.0.0.1:8000/api/notifications/'

class NotificationService {
  async fetchNotifications(params = {}) {
    try {
      const response = await axios.get(API_URL, { params })
      return response.data
    } catch (error) {
      console.error('Error fetching notifications:', error)
      return []
    }
  }

  async acknowledgeNotification(id) {
    try {
      await axios.post(`${API_URL}${id}/acknowledge/`)
    } catch (error) {
      console.error('Error acknowledging notification:', error)
    }
  }

  async deleteNotification(id) {
    try {
      await axios.delete(`${API_URL}${id}/`)
    } catch (error) {
      console.error('Error deleting notification:', error)
    }
  }
}

const notificationService = new NotificationService()
export default notificationService
