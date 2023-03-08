import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useCounterStore = defineStore('settings', () => {
  const settings = ref({})

  return { settings }
})
