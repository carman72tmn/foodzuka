<script setup>
import DefaultLayoutWithVerticalNav from './components/DefaultLayoutWithVerticalNav.vue'
import ModuleErrorBoundary from '@/components/ModuleErrorBoundary.vue'
</script>

<template>
  <DefaultLayoutWithVerticalNav>
    <ModuleErrorBoundary>
      <RouterView />
    </ModuleErrorBoundary>
  </DefaultLayoutWithVerticalNav>
</template>

<style lang="scss">
// As we are using `layouts` plugin we need its styles to be imported
@use "@layouts/styles/default-layout";
</style>
