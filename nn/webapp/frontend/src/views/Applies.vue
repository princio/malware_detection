<template>
  <div class="applies">

    <configs-bar></configs-bar>
    
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
      applies: {},
      model: 'icann',
      wsize: 500,
      windowing: 'both',
      top10m: [ 0, 0 ],
      applies_checked: [],
      replace_value: [],
      cms: [],
      dfs: {},
      fields: {
        applies: {},
        bounds: { min: -100, max: 100 },
        dgas: {},
        sampling: 100,
        th: 50,
      },
      mounted: false,
      values: [],
      models: {},
    };
  },
  async mounted() {
    await this.applies_fetch();

    // this.models = (
    //   await axios.get("http://127.0.0.1:3000/mwdb/model/fetch")
    // ).data.models;

    // this.models = this.models.reduce((map, model) => {
    //   map[model.id] = model;
    //   return map;
    // }, {});

    // await this.fetch_dfs();
    // this.mounted = true;
  },
  methods: {
    applies_changed() {
      if (Object.keys(this.applies).length === 0) return;

      this.applies_checked = Object.keys(this.applies).reduce((aps, hash) => {
        const ap = this.applies[hash];
        ap.hash = hash;
        if (ap.checked) aps.push(ap);
        return aps;
      }, []);
    },
    async apply_delete(hash) {
      this.loading = true;
      axios
        .post("http://127.0.0.1:3000/mwdb/apply/delete", {
          hash: hash,
        })
        .then((res) => {
          this.hash = res.data.hash;
          this.emit_fields();
          this.loading = false;
        })
        .catch(() => {
          this.loading = false;
        });
    },
    async applies_fetch() {
      this.applies = (
        await axios.get("http://127.0.0.1:3000/mwdb/applies")
      ).data.configs;

      console.log(this.applies)

      // for (const h in this.applies) {
      //   const _name = this.applies[h].name;
      //   delete this.applies[h].name;
      //   this.applies[h].name = _name;
      //   this.applies[h].color = 'black';
      //   this.applies[h].checked = true;
      //   this.applies[h].dgas = { 1: false, 2: false, 3: false, all: true };
      // }
    },
    change_dga(hash, dga) {
      this.applies[hash].dgas[dga] = !this.applies[hash].dgas[dga];
      this.applies_changed();
    },
    async fetch_dfs() {
      const df_applies = (
        await axios.post("http://127.0.0.1:3000/mwdb/apply/all", {
          rounder: this.fields.sampling,
        })
      ).data;

      this.dfs = Object.fromEntries(
        Object.keys(df_applies).map((apply_id) => [
          Number(apply_id),
          new dfd.DataFrame(df_applies[apply_id].values, {
            columns: df_applies[apply_id].columns,
          }),
        ])
      );
    },
    updateBarFields(fields) {
      this.fields = fields;
    },
  },
  watch: {
    "fields.sampling": {
      async handler() {
        await this.fetch_dfs();
      },
      deep: true,
    },
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