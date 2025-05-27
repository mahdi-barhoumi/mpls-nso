<script setup></script>

<template>
  <footer class="layout-footer w-full text-xs text-surface-600 dark:text-surface-300 flex flex-col items-center gap-1">
    <span>
      &copy; {{ new Date().getFullYear() }} MPLS-NSO &mdash; All rights reserved.
    </span>
    <span>
      Powered by
      <a href="https://www.djangoproject.com/" target="_blank" class="text-primary underline">Django</a>
      &amp;
      <a href="https://vuejs.org/" target="_blank" class="text-primary underline">Vue.js</a>
    </span>
  </footer>
</template>
