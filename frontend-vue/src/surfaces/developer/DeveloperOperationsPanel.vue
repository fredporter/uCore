<template>
  <section><h2>Developer conversation</h2>
    <p>Discuss {{ repository }} in the shared Developer Chat.</p>
    <button class="usx-btn usx-btn--primary" @click="discuss"><UIcon name="chat" />Open Developer Chat</button>
    <DeveloperChatActivity v-if="chat.repository === repository" />
  </section>
</template>
<script setup lang="ts">
import DeveloperChatActivity from './DeveloperChatActivity.vue'
import { useDeveloperChatStore } from '../../stores/developerChat'
import UIcon from '../../skills/atoms/UIcon.vue'
const props = defineProps<{ repository: string; file?: string }>()
const chat = useDeveloperChatStore()
function discuss() {
  chat.suggestedRepository = props.repository; chat.suggestedFile = props.file || ''
  window.dispatchEvent(new Event('developer-discuss'))
}
</script>
