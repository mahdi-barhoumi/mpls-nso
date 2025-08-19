export const formatUtils = {
  formatPercentage(value) {
    if (value === null || value === undefined) return 'N/A'
    return value.toFixed(1) + '%'
  },

  getPercentage(part, total) {
    if (!total) return '0.0'
    return ((part / total) * 100).toFixed(1)
  },

  formatTimeDetailed(timestamp) {
    if (!timestamp) return 'N/A'
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ${diffMins % 60}m ago`

    return date.toLocaleString()
  },

  getDataAge(timestamp) {
    if (!timestamp) return 'Unknown'
    const diffMs = new Date() - new Date(timestamp)
    const diffMins = Math.floor(diffMs / 60000)

    if (diffMins < 1) return 'Fresh'
    if (diffMins < 5) return 'Recent'
    if (diffMins < 30) return 'Stale'
    return 'Very Stale'
  },

  isDataStale(timestamp) {
    if (!timestamp) return true
    const diffMs = new Date() - new Date(timestamp)
    return diffMs > 300000 // 5 minutes
  },

  formatBytes(bytes) {
    if (!bytes) return '0 B'

    if (bytes < 1024) {
      return bytes.toFixed(0) + ' KB'
    }

    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + sizes[i]
  },
}
