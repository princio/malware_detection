<template>
  <div class="applies">

    <configs-bar v-on:config_changed="config_changed"></configs-bar>
    
  </div>
</template>

<script>
import ConfigBar from "../components/apply/ConfigBar.vue";
// import ApplyPlotBar from "../components/apply/PlotBar.vue";
// import ApplyPlot2 from "../components/apply/Plot2.vue";

const axios = require("axios");
const dfd = require("danfojs/dist/index");

export default {
  name: "Applies",
  components: {
    "configs-bar": ConfigBar,
    // "apply-plot-bar": ApplyPlotBar,
    // "apply-plot-dgas": ApplyPlot2,
  },
  data: function () {
    this.ths_measures = {};
    return {
    };
  },
  async mounted() {
  },
  methods: {
    config_changed() {

    },
  },
  watch: {
  },
};
</script>


<style scoped>
.active {
  background-color: lightskyblue;
}
.boldd {
  font-weight: bold;
  font-size: 16px;
}
.center {
  text-align: center;
  margin: auto;
}
#app > div.applies > table > tbody {
  text-align: left;
}
table > tbody > tr > td,
th {
  text-align: left;
}
</style>