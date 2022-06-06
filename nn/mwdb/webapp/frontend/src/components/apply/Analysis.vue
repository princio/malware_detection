
<template>
  <div id="apply" v-if="apply">
    <table class="center">
      <tbody>
        <tr>
          <td>
            <div class="row">
              <input
                type="range"
                :min="bounds.min"
                :max="bounds.max"
                step=1
                v-on:change="update_cm"
                v-model.number="th"
              />
              <input type="text" style="width:50px"
                v-on:change="update_cm"
                v-model.number="th"
              />
            </div>
          </td>
          <td>
            <div style="display: flex; flex-direction: row;">
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
          </td>
          <td>
            campionamento:
            <div v-if="apply['wtype'] === 'llr'" class="row">
              <input
                type="range"
                :min="5"
                :max="100"
                :step="5"
                v-on:change="fetch_df"
                v-model.number="sampling"
              />
              <input type="text" style="width:50px"
                v-on:change="fetch_df"
                v-model.number="sampling"
              />
            </div>
            <div v-if="apply['wtype'] === 'nx'" class="row">
              <input
                type="range"
                :min="5"
                :max="100"
                :step="1"
                v-on:change="fetch_df"
                v-model.number="sampling"
              />
              <input type="text" style="width:50px"
                v-on:change="fetch_df"
                v-model.number="sampling"
              />
            </div>
          </td>
          <td>
            <div class="row">
              DGAS
              
              <button v-for="dga in [1,2,3]" :key="`btn_dga_${dga}`"
                :class="{ active: dgas[dga] }"
                v-on:click="change_dga(dga)" >
                {{ dga }}
              </button>
            </div>
          </td>
          <td>
          </td>
        </tr>
      </tbody>
    </table>
    <div style="display: flex">
      <span v-if="updating" >
        updating...
      </span>
      <div id="myDiv" class="center"></div>
    </div>
  </div>
</template>

<script>
const dfd = require('danfojs/dist/index')
const Plotly = require('plotly.js-dist')
const axios = require('axios');
const d3 = require('d3');


export default {
  name: "ApplyAnalysis",
  components: {
  },
  props: [ 'apply' ],
  data: function () {
    return {
      execution: "Exec",
      df: null,
      th: 50,
      sampling: 100,
      size: 100,
      top10m: 0,
      windowing: 'resreq',
      dga: 3,
      macro: {},
      normal: {},
      infected: {},
      dgas: { 1: true, 2: true, 3: true },
      cf: {
        tn: 0, tp: 0, fn: 0, fp: 0
      },
      unwindowed: {
        state: false,
        message: "Function not applied"
      },
      bounds: {
        min: 0, max: 100
      },
      plot: undefined,
      tn: 0, tp: 0, fn: 0, fp: 0,
      updating: true
    };
  },
  computed: {
    visual_cm() {
      return {
        tp: (this.tp / (this.tp+this.fn)).toFixed(2),
        tn: (this.tn / (this.tn+this.fp)).toFixed(2),
        fp: (this.fp / (this.tn+this.fp)).toFixed(2),
        fn: (this.fn / (this.tp+this.fn)).toFixed(2),
      }
    }
  },
  methods: {
    async fetch_df() {
      let windows;

      try {
        windows = (await axios.post(`http://127.0.0.1:3000/mwdb/apply/${this.apply.id}`, { rounder: this.sampling })).data;
      } catch (exc) {
        this.unwindowed.state = true;
      }
      if (windows.values.length === 0) {
        this.unwindowed.state = true;
        return null;
      }

      this.df = new dfd.DataFrame(windows.values, { columns: windows.columns });
    },
    get_cm(th) {
      const cm = {
        tn:0, fp:0, fn:0, tp: 0
      };

      const v_wcount = this.df['wcount'].values;
      const v_wvalue = this.df['wvalue'].values;
      const v_dga = this.df['dga'].values;

      for (let j = 0; j < v_dga.length; j++) {
        let l;
        if (v_dga[j] === 0) {
          if (v_wvalue[j] > th) l = 'fp';
          else l = 'tn';
        }
        else if (this.dgas[v_dga[j]]) {
          if (v_wvalue[j] > th) l = 'tp';
          else l = 'fn';
        }
        if (l !== undefined) cm[l] +=  v_wcount[j];
      }

      return cm;
    },
    change_dga(dga) {
      this.dgas[dga] = !this.dgas[dga];
      if (Object.values(this.dgas).reduce((v, t) => v+t, 0) === 0) {
        this.dgas[dga] = !this.dgas[dga];
      } else {
        this.update_all();
      }
    },
    update_all() {
      this.updating = true;
      this.update_cm();
      this.update_plot();
      this.updating = false;
    },
    update_cm() {

      const { tn, fp, fn, tp } = this.get_cm(this.th);

      const normal = {
        pr: tn / (tn + fn),
        re: tn / (tn + fp),
        tnr: tn / (tn + fp),
        f1: null
      }
      normal['f1'] = 2 * (normal.pr * normal.re) / (normal.pr + normal.re);

      const infected = {
        pr: tp / (tp + fp),
        re: tp / (tp + fn),
        tpr: tp / (tp + fn),
        f1: null
      }
      infected['f1'] = 2 * (infected.pr * infected.re) / (infected.pr + infected.re);

      const macro = {
        pr: (normal.pr + infected.pr) / 2,
        re: (normal.re + infected.re) / 2,
        tr: (normal.tnr + infected.tpr) / 2,
        f1: (normal.f1 + infected.f1)/2,
        accuracy: (tp + tn) / (tp + tn + fp + fn)
      }

      this.normal = normal;
      this.infected = infected;
      this.macro = macro;

      this.cf = { tn, fn, fp, tp };

      this.tn = tn;
      this.fn = fn;
      this.fp = fp;
      this.tp = tp;

    },
    async update_plot() {
      this.bounds.min = this.df['wvalue'].min();
      this.bounds.max = this.df['wvalue'].max();
      const step = +((this.bounds.max - this.bounds.min)/this.sampling).toPrecision(2);

      const y_n = [];
      const y_p = [];
      const x = [];

      for (let i = this.bounds.min; i <= this.bounds.max; i += step) {
        const cm = this.get_cm(i);
        
        y_n.push(+(cm.tn / (cm.tn + cm.fp)).toPrecision(2));
        y_p.push(+(cm.tp / (cm.tp + cm.fn)).toPrecision(2));

        x.push(i);
      }

      var trace1 = {
        x,
        y: y_n,
        type: 'scatter',
        name: 'tnr'
      };

      var trace2 = {
        x,
        y: y_p,
        type: 'scatter',
        name: 'tpr'
      };

      var data = [trace1, trace2];

      const f = d3.format('.2s');

      this.plot = await Plotly.newPlot('myDiv', data, {
        width: 800,
        height: 400,
        margins: { l: 10, r: 10, t: 10, b: 10 },
        xaxis: {
          title: 'Threshold',
          showgrid: false,
          zeroline: false,
        },
        yaxis: {

          title: 'True Positive/Negative Ratio',
          showgrid: false,
          zeroline: false,
          fixedranged: true,
          range: [-0.1,1.1]
        },
        shapes: [
          {
            type: 'line',
            x0: x.indexOf(this.th),
            y0: 0,
            x1: x.indexOf(this.th),
            y1: 1,
            line: {
              color: 'grey',
              width: 1.5,
              dash: 'dot'
            }
          }
        ]
      },
      {
        modeBarButtonsToAdd: [
          {
            name: 'download&copy',
            icon: Plotly.Icons.pencil,
            click: (gd) => {
              const dgas = Object.keys(this.dgas).map((dd) => this.dgas[dd] ? dd : '').join('');
              const fn = `plot_${this.apply.wtype}_${this.apply.windowing}_${this.apply.wsize}_${f(this.apply.top10m)}_${dgas}_th${f(this.th).replace('−', '-')}_${this.visual_cm.tp}_${this.visual_cm.tn}`;
              
              const frame = `
              
\\begin{frame}{ww=${this.apply.windowing}, s=${this.apply.wsize}, vDGA=${dgas}, $t^*$=\\numprint{${this.apply.top10m}}}

    \\begin{align*}
        &th = ${f(this.th).replace('−', '-')} \\\\
        &\\begin{pmatrix}
                ${this.visual_cm.tn} & ${this.visual_cm.fp} \\\\
                ${this.visual_cm.fn} & ${this.visual_cm.tp} \\\\
            \\end{pmatrix}
    \\end{align*}
    \\begin{center}
        \\includegraphics[trim={2cm 0 0 3.5cm},clip, width=\\textwidth]{plots/${fn}.jpeg}
    \\end{center}

\\end{frame}
`;
              let textArea = document.createElement("textarea");
              textArea.value = frame;
              // make the textarea out of viewport
              textArea.style.position = "fixed";
              textArea.style.left = "-999999px";
              textArea.style.top = "-999999px";
              document.body.appendChild(textArea);
              textArea.focus();
              textArea.select();
              new Promise((res, rej) => {
                  // here the magic happens
                  document.execCommand('copy') ? res() : rej();
                  textArea.remove();
              });
              
              Plotly.downloadImage(gd, {
                filename: fn,
                format: 'jpeg',
                width: gd._fullLayout.width,
                height: gd._fullLayout.height
              })
            }
          },
        ],
      }
      );

      document.getElementById('myDiv').on('plotly_click', (data) => {

        const point = data.points[0];
        this.th = point.x;

        const f = d3.format('.2s');

        const annotation = {
          text: 'th='+ f(this.th),
          x: point.x,
          y: parseFloat(point.y.toPrecision(4))
        }

        const shape = {
            type: 'line',
            x0: point.x,
            y0: 0,
            x1: point.x,
            y1: 1,
            line: {
              color: 'grey',
              width: 1.5,
              dash: 'dot'
            }
          };

        Plotly.relayout('myDiv', { shapes: [shape], annotations: [ annotation ]})


        this.update_cm();
      });
    }
  },
  updated: function () {
  },
  watch: {
    async apply () {

      this.fetch_df();

      this.update_all();
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