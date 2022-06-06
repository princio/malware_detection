
<template>
  <div id="apply-plot-dgas">
    <div class="center-container">
      {{ fields.dgas }}
      <div
        class="left-brace right-brace"
        v-if="cms.length > 0"
        style="display: flex; flex-direction: row"
      >
        <div>
          <div style="display: flex; flex-direction: row">
            <table style="margin: 0; padding: 0">
              <tbody>
                <tr>
                  <td>{{ visual_cm.all.tn }}</td>
                  <td>{{ visual_cm.all.fp }}</td>
                </tr>
                <!-- <tr>
                  <td>{{ visual_cm[k].fn }}</td>
                  <td>{{ visual_cm[k].tp }}</td>
                </tr> -->
                <tr
                  v-for="k in [1, 2, 3, 'all']"
                  :key="`cm_inf_${k}`"
                  :style="vdga_color(k)"
                >
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
const Plotly = require("plotly.js-dist");
const helpers = require("../../helpers/cm");

const axios = require('axios');
const dfd = require("danfojs/dist/index");

async function fetch_df(hash, rounder) {
  const response = await axios.post(
    'http://127.0.0.1:3000/mwdb/apply/get', {
      hash: hash,
      rounder
  });

  return new dfd.DataFrame(response.data.values, { columns: response.data.columns })
}


export default {
  name: "ApplyPlot2",
  components: {},
  props: ["applies", "fields"],
  data: function () {
    this.cms = [];
    this.bounds = { max: 100, min: 0 };
    return {
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
      return helpers.get_ths(
        this.bounds.max,
        this.bounds.min,
        this.fields.sampling
      );
    },
    cm() {
      return this.cms[this.idx];
    },
    visual_cm() {
      return helpers.cm_relative(this.cm);
    },
  },
  async mounted() {
    await this.get_cms();
    await this.generate_plot();
  },
  methods: {
    set_bounds(dfs) {
      let max = 0;
      let min = 0;

      for (const df of dfs) {
        if (max < df.max()) max = df.max();
        if (min > df.min()) min = df.min();
      }

      this.bounds.max = 100000;
      this.bounds.min = -100000;
    },
    vdga_color(vdga) {
      return { color: helpers.vdga_colors[vdga] };
    },
    async get_cms() {
      if (this.applies.length === 0) {
        this.cms = [];
      }
      else {
        const _dfs = [];

        for (const apply of this.applies) {
          _dfs.push(await fetch_df(apply.hash, this.fields.rounder))
        }

        this.set_bounds(_dfs);

        if (_dfs.length > 0) {
          this.cms = helpers.get_cms(_dfs, this.ths);
        }
      }
    },
    generate_plot() {
      if (this.cms.length === 0) return;

      const applies = this.applies;

      if (applies.length === 0) return;

      console.log(this.fields);

      const { data, layout, options } = helpers.get_plotly2(
        this.cms,
        this.ths,
        this.th,
        applies,
        this.fields
      );

      Plotly.newPlot("plotDiv", data, layout, options).then(() => {
        document.getElementById("plotDiv").on("plotly_click", async (data) => {
          const point = data.points[0];
          this.fields.th = point.x;
        });
      })
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
    applies: {
      async handler() {
        console.log('ciao');
        await this.get_cms();
        await this.generate_plot();
      },
    },
    "fields.th": {
      async handler() {
        if (this.cms.length === 0) return;
        const { annotation, shape } = helpers.get_plotly_annotations_for_th(
          this.ths[this.idx]
        );
        await Plotly.relayout("plotDiv", {
          shapes: [shape],
          annotations: [annotation],
        });
      },
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