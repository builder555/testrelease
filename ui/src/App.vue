<script setup>
import TheOctocat from './components/TheOctocat.vue'
</script>

<template>
  <the-octocat />
  <form @submit.prevent="sendMessage(message)">
    <input type="text" id="message" placeholder="Enter message" v-model="message" />
    <button type="submit">Send</button>
  </form>
  <ul>
    received:
    <li v-for="message in messages" :key="message">{{ message }}</li>
  </ul>
</template>

<script>
export default {
  data: () => ({
    messages: [],
    message: '',
    socket: null,
  }),
  methods: {
    sendMessage(message) {
      this.socket.send(message);
      this.message = '';
    }
  },
  mounted() {
    this.socket = new WebSocket('ws://localhost:12999');
    this.socket.onmessage = (event) => {
      this.messages.push(event.data);
    };
  }
}
</script>

<style scoped>
</style>
