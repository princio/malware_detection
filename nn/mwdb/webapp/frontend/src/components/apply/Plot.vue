
<template>
  <div id="apply-plot" v-if="apply">
    <div class="center-container">
      <div v-if="cm" style="display: flex; flex-direction: row; width: 100px;">
        <div style="font-size: 48px">(</div>
          <table style="margin: 0; padding: 0;">
            <tbody>
              <tr>
                <td>{{ visual_cm.tn }}</td>
                <td>{{ visual_cm.fp }}</td>
              </tr>
              <tr>
                <td>{{ visual_cm.fn }}</td>
                <td>{{ visual_cm.tp }}</td>
              </tr>
            </tbody>
          </table>
          <div style="font-size: 48px">)</div>
      </div>
      <div id="myDiv" class="center"></div>
    </div>
  </div>
</template>

<script>
const dfd = require('danfojs/dist/index')
const Plotly = require('plotly.js-dist')
const axios = require('axios');
const helpers = require('../../helpers/cm');


export default {
  name: "ApplyPlot",
  components: {
  },
  props: {
    apply: {
      type: Object,
      default: function () {
        return undefined;
      }
    },
    fields: {
      type: Object,
      default: function () {
        return {
          th: 50,
          sampling: 100,
          dgas: { 1: true, 2: true, 3: true },
          bounds: { min: -100, max: 100 }
        }
      }
    }
  },
  data: function () {
    return {
      df: null,
      updating: true,
      plot: { x: [50], y_p: [], y_n: []},
      cms: [ { th: 50, cm: undefined } ]
    };
  },
  computed: {
    th() {
      return this.plot.x[this.plot.x.findIndex((_th) => _th >= this.fields.th)];
    },
    cm() {
      return this.cms[this.plot.x.indexOf(this.th)].cm;
    },
    visual_cm() {
      const cm = this.cm;
      return {
        tp: (cm.tp / (cm.tp+cm.fn)).toFixed(2),
        tn: (cm.tn / (cm.tn+cm.fp)).toFixed(2),
        fp: (cm.fp / (cm.tn+cm.fp)).toFixed(2),
        fn: (cm.fn / (cm.tp+cm.fn)).toFixed(2),
      }
    }
  },
  methods: {
    async fetch_df() {
      const windows = (await axios.post(`http://127.0.0.1:3000/mwdb/apply/${this.apply.id}`, { rounder: this.fields.sampling })).data;
      this.df = new dfd.DataFrame(windows.values, { columns: windows.columns });
    },
    async generate_plot() {
      this.cms = helpers.get_cms(this.df, this.fields);

      this.plot = helpers.calculate_plot(this.cms, true);

      const { data, layout, options } = helpers.get_plotly(this.plot, this.th);
      
      await Plotly.newPlot('myDiv', data, layout, options);

      document.getElementById('myDiv').on('plotly_click', async (data) => {
        const point = data.points[0];
        this.fields.th = point.x;
        await this.change_th();
      });
    },
    generate_frame() {
      const div = document.getElementById('myDiv');
      
      const { frame, fn } = helpers.generate_frame(this.apply, this.visual_cm, this.fields);

      helpers.copy2clipboard(document, frame);
      Plotly.downloadImage(div, {
          filename: fn,
          format: 'jpeg',
          width: div._fullLayout.width,
          height: div._fullLayout.height
      });
    },
    async change_th() {
      const { annotation, shape } = helpers.get_plotly_annotations_for_th(this.th);
      await Plotly.relayout('myDiv', { shapes: [shape], annotations: [ annotation ]})
    }
  },
  watch: {
    apply: {
      async handler() {
        this.updating = true;
        await this.fetch_df();
        await this.generate_plot();
        this.updating = false;
      },
      deep: true
    },
    'fields.th': {
      async handler(old_th, th) {
        const i = this.plot.x.findIndex((_th) => _th >= th);
        th = this.plot.x[i];
        await this.change_th();
      }
    },
    'fields.sampling': {
      async handler() {
        this.updating = true;
        await this.fetch_df();
        await this.generate_plot();
        this.updating = false;
      }
    },
    'fields.dgas': {
      handler() {
        this.generate_plot();
      },
      deep: true
    },
    'fields.bounds': {
      handler() {
        this.generate_plot();
      },
      deep: true
    }
  }
};
</script>

<style>
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
table, .dataframe {
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