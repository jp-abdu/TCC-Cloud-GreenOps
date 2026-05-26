import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

export const getRegions = () => client.get('/regions')
export const getInstances = () => client.get('/instances')
export const getBenchmarks = () => client.get('/benchmarks')

export const calculateInstance = (data) => client.post('/calculate/instance', data)
export const calculateArchitecture = (data) => client.post('/calculate/architecture', data)