
<template>
  <div id="apply-plot-dgas" v-if="apply">
    <div class="center-container">
      <div
        class="left-brace right-brace"
        v-if="cms.length > 0"
        style="display: flex; flex-direction: row;"
        >
        <div>
          <div
            style="display: flex; flex-direction: row;">
            <table style="margin: 0; padding: 0;">
              <tbody>
                <tr>
                  <td>{{ visual_cm.all.tn }}</td>
                  <td>{{ visual_cm.all.fp }}</td>
                </tr>
                <!-- <tr>
                  <td>{{ visual_cm[k].fn }}</td>
                  <td>{{ visual_cm[k].tp }}</td>
                </tr> -->
                <tr v-for="k in [ 1, 2, 3, 'all' ]"
                  :key="`cm_inf_${k}`"
                  :style="vdga_color(k)">
                    <td>{{ visual_cm[k].fn }}</td>
                    <td>{{ visual_cm[k].tp }}</td>
                  </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <div id="plotDiv" class="center"></div>
    </div>
  </div>
</template>

<script>
const dfd = require("danfojs/dist/index");
const Plotly = require("plotly.js-dist");
const axios = require("axios");
const helpers = require("../../helpers/cm");

export default {
  name: "ApplyPlotDGAs",
  components: {},
  props: {
    apply: {
      type: Object,
      default: function () {
        return undefined;
      },
    },
    fields: {
      type: Object,
      default: function () {
        return {
          th: 50,
          sampling: 100,
          dgas: { 1: true, 2: true, 3: true },
          bounds: { min: -100, max: 100 },
        };
      },
    },
  },
  data: function () {
    this.cms = [];
    return {
      df: null,
      updating: true,
    };
  },
  computed: {
    idx() {
      return this.ths.findIndex((th) => th >= this.fields.th);
    },
    th() {
      return this.ths[this.idx];
    },
    ths() {
      return helpers.get_ths(this.fields);
    },
    cm() {
      return this.cms[this.idx];
    },
    visual_cm() {
      return helpers.cm_relative(this.cm);
    },
  },
  methods: {
    vdga_color(vdga) {
      return { color: helpers.vdga_colors[vdga] };
    },
    async fetch_df() {
      const windows = (
        await axios.post(`http://127.0.0.1:3000/mwdb/apply/${this.apply.id}`, {
          rounder: this.fields.sampling,
        })
      ).data;
      this.df = new dfd.DataFrame(windows.values, { columns: windows.columns });
    },
    async generate_plot() {
      this.cms = helpers.get_cms(this.df, this.ths);

      const { data, layout, options } = helpers.get_plotly2(
        this.cms,
        this.ths,
        this.th
      );

      await Plotly.newPlot("plotDiv", data, layout, options);

      document.getElementById("plotDiv").on("plotly_click", async (data) => {
        const point = data.points[0];
        this.fields.th = point.x;
      });
    },
    generate_frame() {
      const div = document.getElementById("plotDiv");

      const { frame, fn } = helpers.generate_frame(
        this.apply,
        this.visual_cm,
        this.fields
      );

      helpers.copy2clipboard(document, frame);
      Plotly.downloadImage(div, {
        filename: fn,
        format: "jpeg",
        width: div._fullLayout.width,
        height: div._fullLayout.height,
      });
    },
  },
  watch: {
    apply: {
      async handler() {
        this.updating = true;
        await this.fetch_df();
        await this.generate_plot();
        this.updating = false;
      },
      deep: true,
    },
    "fields.th": {
      async handler() {
        const { annotation, shape } = helpers.get_plotly_annotations_for_th(
          this.ths[this.idx]
        );
        await Plotly.relayout("plotDiv", {
          shapes: [shape],
          annotations: [annotation],
        });
      },
    },
    "fields.sampling": {
      async handler() {
        this.updating = true;
        await this.fetch_df();
        await this.generate_plot();
        this.updating = false;
      },
    },
    "fields.dgas": {
      handler() {
        this.generate_plot();
      },
      deep: true,
    },
    "fields.bounds": {
      handler() {
        this.generate_plot();
      },
      deep: true,
    },
  },
};
</script>

<style>
.left-brace {
  display: flex;
  flex-direction: row;
  border-left: 4px solid;
  border-top-left-radius: 10px 50px;
  border-bottom-left-radius: 10px 50px;
}
.right-brace {
  display: flex;
  flex-direction: row;
  border-right: 4px solid;
  border-top-right-radius: 10px 50px;
  border-bottom-right-radius: 10px 50px;
}
.active {
  background-color: lightskyblue;
}
.left {
  text-align: left;
}
.center {
  text-align: center;
  margin: auto;
}
.center-container {
  display: flex;
  flex-direction: column;
  justify-content: space-around;
  align-items: center;
}
.nopadding {
  padding: 0;
  margin: auto;
  text-align: left;
  margin: auto;
}
.greenclass {
  color: yellowgreen;
}
.redclass {
  color: red;
}
.btn {
  border: 0;
  background-color: transparent;
  color: white;
  font-size: 10px;
}
.column {
  display: flex;
  flex-direction: column;
  justify-content: space-around;
  width: 100%;
  text-align: left;
}
.row {
  display: flex;
  flex-direction: row;
}
table > tbody > tr > td {
  vertical-align: middle;
  text-align: center;
  padding: 0 10px;
}
table > tbody > tr > th {
  text-align: left;
  padding: 0 20px;
}
table,
.dataframe {
  border: 0 !important;
  padding: 50px 0px 0 0;
}
body {
  margin: 0;
  background-color: rgb(53, 53, 53);
}
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: white; /*#2c3e50;*/
  padding: 20px;
}
th,
td {
  vertical-align: top;
}
</style>