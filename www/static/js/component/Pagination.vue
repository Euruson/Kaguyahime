<template>
  <ul class="uk-pagination">
    <li v-if="! page.has_previous" class="uk-disabled">
      <span>
        <i uk-icon="chevron-left"></i>
      </span>
    </li>
    <li v-if="page.has_previous">
      <a v-on:click.stop="$emit('go-to-previous-page')" href="#0">
        <i uk-icon="chevron-left"></i>
      </a>
    </li>
    <li class="uk-active">
      <span v-text="page.page_index"></span>
    </li>
    <li v-if="! page.has_next" class="uk-disabled">
      <span>
        <i uk-icon="chevron-right"></i>
      </span>
    </li>
    <li v-if="page.has_next">
      <a v-on:click.stop="$emit('go-to-next-page')" href="#0">
        <i uk-icon="chevron-right"></i>
      </a>
    </li>
  </ul>
</template>

<script>
export default {
  name: "Pagination",
  props: ["page"]
};
</script>
