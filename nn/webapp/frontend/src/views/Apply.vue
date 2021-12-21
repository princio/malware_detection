<template>
  <div class="apply">
    <div class="center">
      <apply-info v-if="show_infos" ref="apply_info" :apply="apply"></apply-info>
      <apply-analysis ref="apply_analysis" :apply="apply"></apply-analysis>
    </div>
  </div>
</template>

<script>
import ApplyAnalysis from '../components/apply/Analysis.vue';
import ApplyInfo from '../components/apply/Info.vue';

const axios = require('axios');

export default {
  name: 'ApplyView',
  components: {
    'apply-analysis': ApplyAnalysis,
    'apply-info': ApplyInfo
  },
  props: [ 'apply_id', 'show_infos' ],
  data: function () {
    return {
      apply: undefined
    };
  },
  async created() {
    this.apply = (await axios.get('http://127.0.0.1:3000/mwdb/apply/get/' + this.apply_id)).data.apply;
  },
  methods: {
  },
  watch: {
    async apply_id () {
      this.apply = (await axios.get('http://127.0.0.1:3000/mwdb/apply/get/' + this.apply_id)).data.apply;
    }
  }
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