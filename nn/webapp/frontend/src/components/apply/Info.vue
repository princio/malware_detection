<template>
  <div class="apply_info">
    <span v-if="apply === undefined">
        loading...
    </span>
    <table v-else
    class="center"
      ref="apply_table">
      <thead>
        <tr >
          <th>ID</th>
          <th>NAME</th>
          <th>TOP10M</th>
        </tr>
      </thead>
      <tbody ref="apply_table_body">
        <tr>
          <td>{{ apply.id }}</td>
          <td>{{ apply.name }}</td>
          <td>{{ apply.top10m }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>

export default {
  name: 'ApplyInfo',
  components: {
  },
  props: [ 'apply' ],
  data: function () {
    return {
    };
  },
  async created() {
  },
  methods: {
  },
}
</script>


<style scoped>
.center {
  text-align: center;
  margin: auto;
}
#app > div.applies > table > tbody {
  text-align: left;
}
</style>