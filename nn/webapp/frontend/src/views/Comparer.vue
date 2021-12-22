
<template>
  <div id="comparer">
    <div ref="toolbar" class="column">
      <div class="row">
        <div class="column">
          <h4>$size$</h4>
          <div class="column">
            <div v-for="size in sizes" :key="size">
              <input
                type="checkbox"
                :id="size"
                :value="size"
                v-model="checkedSizes"
              />
              <label :for="size">{{ size }} </label>
            </div>
          </div>
        </div>
        <div class="column">
          <h4>$vDGA$</h4>
          <div class="column">
            <div v-for="dga in dgas" :key="dga">
              <input
                type="checkbox"
                :id="dga"
                :value="dga"
                v-model="checkedDgas"
              />
              <label :for="dga">{{ dga }} </label>
            </div>
          </div>
        </div>
        <div class="column">
          <h4>$f$</h4>
          <div class="column">
            <div v-for="fx in fxs" :key="fx">
              <input type="checkbox" :id="fx" :value="fx" v-model="checkedFxs" />
              <label :for="fx">{{ fx_symbol(fx) }} </label>
            </div>
          </div>
        </div>
        <div class="column">
          <h4>$norm$</h4>
          <div class="column">
            <div>
              <input type="radio" id="norm_no" :value="false" v-model="normalized" />
              <label for="norm_no">$no$</label>
            </div>
            <div>
              <input type="radio" id="norm_yes" :value="true" v-model="normalized" />
              <label for="norm_yes">$yes$</label>
            </div>
          </div>
        </div>
      </div>
      <div style="margin: 15px">
        <div class="column">
          <table class="nopadding">
            <thead>
              <tr>
                <th></th>
                <th v-for="size in sizes" :key="`table_th_size_${size}`">
                  {{ size }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="fx in fxs" :key="`table_th_fx_${fx}`">
                <th>{{ fx_symbol(fx) }}</th>
                <td v-for="size in sizes" :key="`table_th_size_${size}`">
                  <select name="select_dga" id="select_dga" v-model="ths_dgas[fx][size].dga">
                    <option v-for="dga in dgas" :key="`select_dga_${fx}_${size}_${dga}`">{{ dga }}</option>
                  </select>
                  <select name="select_th" id="select_th" v-model="ths_dgas[fx][size].measure">
                    <option v-for="measure in Object.keys(ths_measures[fx][size][ths_dgas[fx][size].dga])" :key="`select_dga_${fx}_${size}_${measure}`">{{ measure }}</option>
                  </select>
                  <button
                    v-on:click="set_ths_with_same_dgas(fx, size)"
                  >
                  set</button>
                </td>
              </tr>
              <tr>
                <th>all</th>
                <td colspan=3 class="left">
                  <button v-on:click="set_ths_to_type('sum')" >sum</button>
                  <button v-on:click="set_ths_to_type('ninf')" >!inf</button>
                  <button v-on:click="set_ths_to_type('inf')" >inf</button>
                  <button v-on:click="set_ths_to_type('gt08')" >gt08</button>
                  <button v-on:click="set_ths_to_type('gt05')" >gt05</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <button v-on:click="reload()">Reload</button>
      <button v-on:click="render()">Render</button>
      <button v-on:click="tolatex()">$\LaTeX$</button>
    </div>
    <div ref="legend">
      <h3>
        Legend:
        <button v-on:click="toggle_legend()">{{ legend_btn_label }}</button>
      </h3>
      <table v-show="legend_show" style="text-align: left; margin: auto">
        <thead>
          <th>Name</th>
          <th>Type</th>
          <th>Description</th>
        </thead>
        <tbody>
          <tr>
            <td>$s$</td>
            <td>size</td>
            <td>Window size, it could be $100$, $500$, $2500$.</td>
          </tr>
          <tr>
            <td>$\bar{M}^s_f$</td>
            <td>threshold</td>
            <td>
              Maximum of not infected windows having size $s$ for the function
              $f$.
            </td>
          </tr>
          <tr>
            <td>$th_f$</td>
            <td>threshold refiner</td>
            <td>
              Coefficient which is multiplied to $\bar{M}^s_f$ to refine the
              inspection.
            </td>
          </tr>
          <tr>
            <td>$\lambda$</td>
            <td>function</td>
            <td>
              A window is infected if its $LLR$ (aka $\lambda$) is greater than
              $\bar{M}^s_{\lambda} \cdot th_{\lambda}$.
            </td>
          </tr>
          <tr>
            <td>$nx$</td>
            <td>function</td>
            <td>
              A window is infected if it counts of domains responses is greater
              than $\bar{M}^s_{gt} \cdot th_{nx}$.
            </td>
          </tr>
          <tr>
            <td>$gt_{0.9}$</td>
            <td>function</td>
            <td>
              A window is infected if it counts of domains having inference
              greater than 0.9 is greater than $\bar{M}^s_{gt_{0.9}}$.
            </td>
          </tr>
          <tr>
            <td>$n_p$</td>
            <td>value</td>
            <td>Number of pcaps processed. This value depends on $vDGA$.</td>
          </tr>
          <tr>
            <td>$n_p^d$</td>
            <td>value</td>
            <td>
              Number of pcaps processed having at least one window infected.
            </td>
          </tr>
          <tr>
            <td>$N_w$</td>
            <td>value</td>
            <td>
              It is a normalized value which indicates <i>when</i> the first
              infected window has been detected.<br />$0$ indicates the first
              window, $1$ the last one.
            </td>
          </tr>
          <tr>
            <td>$n_w$</td>
            <td>value</td>
            <td>The total number of windows for the considered pcaps.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div ref="bounds">
      <h3>
        Bounds:
        <button v-on:click="toggle_bounds()">{{ bounds_btn_label }}</button>
      </h3>
      <div
      v-show="bounds_show" 
      style="
        display: flex;
        flex-direction: row;
        width: 100%;
        justify-content: space-around;
      "
      v-html="compiledBounds"></div>
    </div>

    <div
      id="df_table"
      style="
        display: flex;
        flex-direction: row;
        width: 100%;
        justify-content: space-around;
      "
      ref="mathJaxEl"
      v-html="compiledHtml"
    ></div>

    <table
    class="center"
      ref="cms_table">
      <thead>
        <tr >
          <th style='width: 60px;' v-for="(h, hindex) in header" :key="`header_${hindex}`">
            <div class="column">
              <span style="height: 40px;">
                {{ h }}
              </span>
              <div>
                <button class="btn" v-on:click="setHSort(hindex, false)">
                  <font-awesome-icon :icon="['fas', 'sort-numeric-up-alt']" />
                  </button>
                <button class="btn" v-on:click="setHSort(hindex, true)">
                  <font-awesome-icon :icon="['fas', 'sort-numeric-down']" />
                </button>
              </div>
            </div>
          </th>
        </tr>
      </thead>
      <tbody ref="cms_table_body">
        <tr v-for="(row, rindex) in sortedArray" :key="`row_${rindex}`">
          <th
          v-for="(c, cindex) in row.slice(0, 3)"
          :key="`col_index_${rindex}_${cindex}`"
          >
            {{ c }}
          </th>
          <td>
            <div class="row">
              <input
                type="range"
                :name="`${row[0]}_${row[1]}_th`"
                :id="`${row[0]}_${row[1]}_th`"
                :min="thsbounds[row[0]][row[1]][row[2]].min"
                :max="thsbounds[row[0]][row[1]][row[2]].max"
                :step="1"
                v-on:change="reload"
                v-model.number="ths[row[0]][row[1]][row[2]]"
              />
              <input type="text" style="width:50px"
                v-on:change="reload"
                v-model.number="ths[row[0]][row[1]][row[2]]"
              />
            </div>
          </td>
          <td
          v-for="(c, cindex) in row.slice(4)"
          :key="`col_value_${rindex}_${cindex}`"
          :class="c > 0.75 ? 'greenclass' : (c < 0.25 ? 'redclass' : null)"
          >
          {{ c }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
const dfd = require('danfojs/dist/index')
const axios = require('axios');

const SIZES = [ 100, 500, 2500 ];
const FXS = ["llr", "nx", "gt09", 'llrt' ];
const DGAS = [ 0,1,2,3 ];


function get_row(cm, normalized = true) {
  const _2d = (n) => (n >= 0.99 && n < 1) ? 0.99 : ((n > 0 && n <= 0.01) ? 0.01 : n.toFixed(2));

  const _print = (n, reverse=false, color=true) => {
    let t;
    let colors = [ 'red', 'YellowGreen' ];
    if (reverse)
      colors = colors.reverse();

    n = _2d(n);

    if (n == 1) t = `1`;
    else
    if (n == 0) t = `0`;
    else
      t = `${n}`.slice(1)

    if (color) {
      if (isNaN(n)) t = '{\\color{yellow}-}';
      
      if (n <= 0.5)
        t = `{\\color{${colors[0]}} ${t}}`
      else
      if (n >= 0.5)
        t = `{\\color{${colors[1]}} ${t}}`
    }
    return t;
  };

  let tn = cm.cm.tn;
  let fn = cm.cm.fn;
  let fp = cm.cm.fp;
  let tp = cm.cm.tp;
  if (normalized) {
    const p = cm.cm.tp + cm.cm.fn;
    const n = cm.cm.tn + cm.cm.fp;
    tn = _print(tn/n);
    fp = _print(fp/n, true, false);
    fn = _print(fn/p, true, false);
    tp = _print(tp/p);
  }

  const col1 = `$\\small\\begin{pmatrix} ${tn} & ${fp} \\\\ ${fn} & ${tp} \\end{pmatrix}$`;


  return [
    cm.r.fx,
    cm.r.size,
    cm.r.dga,
    cm.cm.th,
    col1,
    _2d(cm.cm.report.normal.tpr),
    _2d(cm.cm.report.infected.tpr),
    _2d(cm.cm.report.macro.accuracy),
  ];
} //end get_row

export default {
  name: "App",
  components: {},
  data: function () {
    const ths = {};
    const ths_dgas = {};
    const ths_measures = {};
    for (const fx of FXS) {
      ths[fx] = {};
      ths_dgas[fx] = {};
      ths_measures[fx] = {};
      for (const size of SIZES) {
        ths_dgas[fx][size] = { measure: 'mean', dga: 0 }
        ths[fx][size] = {};
        ths_measures[fx][size] = {};
        for (const dga of DGAS) {
          ths[fx][size][dga] = 1;
          ths_measures[fx][size][dga] = { mean: 0 }
        }
      }
    }
    this.ths_measures= ths_measures
    return {
      bests_text: "find best",
      bounds: "",
      bounds_show: false,
      checkedSizes: [100],
      checkedDgas: [1, 2, 3],
      checkedFxs: ["llr"],
      cms: {},
      dgas: [0, 1, 2, 3],
      dga_gt: false,
      hasc: true,
      hindex: 1,
      input: "",
      legend_show: false,
      normalized: true,
      ths: ths,
      ths_dgas: ths_dgas,
      th_p: 0.5,
      values: [],
    };
  },
  created() {
    this.fxs = FXS;
    this.sizes = SIZES;
    this.header = [
      '$f$',
      '$s$',
      '$vDGA$',
      '$th$',
      '$\\tiny\\begin{pmatrix} tn & fp \\\\ fn & tp \\end{pmatrix}$',
      '$\\bar{tpr}$',
      '$tpr$',
      '$acc$'
    ];
    this.dfs = {};
    this.measures = [ 'sum', 'inf', 'ninf', 'gt05', 'gt08', 'max', 'min', 'mean' ];
  },
  async mounted() {
    this.renderMathJax([this.$refs.toolbar]);

    for (const fx of this.fxs) {
      if (fx === 'ratio') continue;
      
      this.cms[fx] = []
      this.dfs[fx] = await dfd.read_csv(`http://127.0.0.1:3000/csv/${fx}.csv`);
    }

    this.ths_measures = (await axios.get('http://127.0.0.1:3000/csv/measures.json')).data;
    
    this.set_ths_to_type('mean');

    this.reload();
    this.render();
  },
  computed: {
    compiledHtml: function () {
      return this.input;
    },
    compiledBounds: function () {
      return this.bounds;
    },
    legend_btn_label: function () {
      return this.legend_show ? "Hide" : "Show";
    },
    bounds_btn_label: function () {
      return this.bounds_show ? "Hide" : "Show";
    },
    th_measure_sym: function () {
      return {
        mean: '\\bar{\\mu}',
        max: '\\bar{M}'
      }
    },
    thsbounds: function() {
      const ths = {};
      for (const fx of FXS) {
        ths[fx] = {}
        for (const size of SIZES) {
          ths[fx][size] = {}
          let min = Math.min(...Object.keys(this.ths_measures[fx][size]).map((dga) => this.ths_measures[fx][size][dga].min));
          let max = Math.max(...Object.keys(this.ths_measures[fx][size]).map((dga) => this.ths_measures[fx][size][dga].max));
          for (const dga of [ 1, 2, 3 ]) {
            ths[fx][size][dga] = {
              min,
              max
            }
          }
        }
      }
      return ths;
    },
    sortedArray: function() {
      return this.values.slice().sort((r1, r2) => {
        let a = r1[this.hindex];
        a = a === 'NaN' ? -1 : a;
        let b = r2[this.hindex];
        b = b === 'NaN' ? -1 : b;
        return (this.hasc ? (a - b) : (b - a))
      });
    },
  },
  methods: {
    async setHSort(hindex, asc) {
      this.hindex = hindex;
      this.hasc = asc;
    },
    get_cm(fx, size, dga, th) {
      let df = this.dfs[fx];
      df = df.query({ condition: df['size'].eq(Number(size)).and(df['dga'].eq(0).or(df['dga'].eq(Number(dga)))) });
      
      df.addColumn({ column: 'detected', values: df[fx].gt(th), inplace: true });
      
      const s_det = df['detected']
      const s_ndet = df['detected'].apply((x) => !x)

      const tn = df['window'].loc(s_ndet.and(df['dga'].eq(0))).sum();
      const fp = df['window'].loc( s_det.and(df['dga'].eq(0))).sum();
      const fn = df['window'].loc(s_ndet.and(df['dga'].eq(dga))).sum();
      const tp = df['window'].loc( s_det.and(df['dga'].eq(dga))).sum();

      let normal = {
        pr: tn / (tn + fn),
        re: tn / (tn + fp),
        tpr: tn / (tn + fp)
      }
      normal['f1'] = 2 * (normal.pr * normal.re) / (normal.pr + normal.re);

      const infected = {
        pr: tp / (tp + fp),
        re: tp / (tp + fn),
        tpr: tp / (tp + fn)
      }
      infected['f1'] = 2 * (infected.pr * infected.re) / (infected.pr + infected.re);

      const macro = {
        pr: (normal.pr + infected.pr) / 2,
        re: (normal.re + infected.re) / 2,
        tpr: (normal.tpr + infected.tpr) / 2,
        f1: (normal.f1 + infected.f1)/2,
        accuracy: (tp + tn) / (tp + tn + fp + fn)
      }

      return {
        r: { fx, size, dga },
        cm: {
          th,
          tn, fp, fn, tp,
          report: { normal, infected, macro }
        }
      };
    },
    clearMathJax() {
      const nodes = {}
      for (const node of window.MathJax.startup.document.getMathItemsWithin(this.$refs.cms_table_body)) {
        const cellIndex = node.end.node.parentElement.parentElement.rowIndex;
        if (cellIndex in nodes) {
          nodes[cellIndex].remove();
          nodes[cellIndex] = node.end.node;
        }
        else
          nodes[cellIndex] = node.end.node;
      }
    },
    get_cms() {
      const cms = [];
      for (const fx of this.checkedFxs) {
        if (fx === 'ratio') continue;
        for (const size of this.checkedSizes) {
          for (const dga of this.checkedDgas) {
            const th = this.ths[fx][size][dga];
            cms.push(this.get_cm(fx, size, dga, th));
          }
        }
      }
      return cms;
    },
    async update_row(index) {
      const row = this.values[index];
      const cm = this.get_cm(row[0], row[1], row[2]);
      this.values[index] = get_row(cm, this.normalized);
    },
    async reload() {
      this.values = this.get_cms().map((cm) => get_row(cm, this.normalized));
      await this.$nextTick();
      this.clearMathJax();
      this.renderMathJax([this.$refs.cms_table_body]);
    },
    set_ths_to_type(type) {
      for (const fx of this.fxs) {
        for (const size of this.sizes) {
          for (const dga of [ 1,2,3 ]) {
            this.ths[fx][size][dga] = this.ths_measures[fx][size][dga][type];
          }
        }
      }
      this.reload()
    },
    set_ths_with_same_dgas(fx, size) {
      const dga_chosen = this.ths_dgas[fx][size].dga;
      const thmm_chosen = this.ths_dgas[fx][size].measure;
      const m = this.ths_measures[fx][size][dga_chosen][thmm_chosen]
      for (const dga of this.dgas) {
        this.ths[fx][size][dga] = m;
      }
      this.reload()
    },
    fx_symbol(fx) {
      return {
        'llr': '$\\lambda$',
        'nx': '$nx$',
        'gt09': '$gt_{0.9}$',
        'ratio': '$p$',
        'llrt': '$\\lambda_l$',
      }[fx]
    },
    toggle_legend() {
      this.legend_show = !this.legend_show;
    },
    toggle_bounds() {
      this.bounds_show = !this.bounds_show;
    },
    render() {
      this.renderMathJax([this.$refs.toolbar]);
      this.renderMathJax([this.$refs.mathJaxEl]);
      if (this.legend_show)
        this.renderMathJax([this.$refs.legend]);
      if (this.bounds_show)
        this.renderMathJax([this.$refs.bounds]);
      this.renderMathJax([this.$refs.cms_table]);
    },
    renderMathJax(refs = [this.$refs.mathJaxEl]) {
      if (!refs ||  refs.length === 0 || !refs[0])
        return
      if (window.MathJax && window.MathJax.typesetPromise)
          window.MathJax.typesetPromise(refs);
    },
    tolatex() {
      let lx = `\\begin{tabular}{lllcrrrr}\n`
      for (const row of this.values) {
        for (const idx in row) {
          let value = row[idx];
          if (idx == 3) {
            value = Number.parseFloat(row[idx] / this.ths_measures[row[0]][row[1]][0].max).toFixed(2);
            value = `{\\small$${value}\\cdot\\bar{M}$}`
          }
          if (typeof(value) == 'string') 
            lx += ` ${value.replaceAll('YellowGreen', 'OliveGreen')} &`
          else
            lx += ` ${value} &`
        }
        lx = lx.substring(0, lx.length-1) + `\\\\\n`
      }
      lx += `\\end{tabular}`
      navigator.clipboard.writeText(lx).then(function() {
        console.log('Async: Copying to clipboard was successful!');
      }, function(err) {
        console.error('Async: Could not copy text: ', err);
      });
    }
  },
  updated: function () {
    this.$nextTick(function () {
      if(this.renderTable) {
        this.renderMathJax([this.$refs.cms_table_body]);
        this.clearMathJax();
        this.renderTable = false;
      }
    })
  },
  watch: {
    sortedArray: function() {
      this.renderTable = true;
    },
    ths: function() {
      this.reload()
    }
  }
};
</script>

<style>
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
  font-size: 20px;
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