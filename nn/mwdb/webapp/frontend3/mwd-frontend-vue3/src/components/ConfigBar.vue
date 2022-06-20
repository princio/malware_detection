<script lang="ts">
import axios from "axios";
import { defineComponent } from "vue";
import Plotly from "plotly";
import { plot_scatter } from "../assets/plotter";

type ReplaceValue = ["llr" | "nx", [number, number], [string, string]];
interface Configs {
  models: string[];
  wsize: number[];
  windowing: string[];
  top10m: [number, number][];
  replace_values: ReplaceValue[];
}

interface Config {
  model: "none" | "icann" | "tld" | "private" | "nx";
  wsize: 100 | 500 | 2500;
  windowing: "req" | "res" | "both";
  top10m: [number, number];
  replace_values: ReplaceValue;
}

interface CMS {
  ths: number[];
  cms: {
    tn: number[];
    tp: [number[], number[], number[]];
  };
}

const rv_type = (config: Config) => (config.model === "nx" ? "nx" : "llr");

export default defineComponent({
  name: "ConfigBar",
  emits: {
    configsChanged(payload: { configs: [Config, Config] }) {
      return payload.configs;
    },
  },
  data: function () {
    return {
      all_configs: {} as Configs,
      config_0: {
        model: "icann",
        wsize: 500,
        windowing: "both",
        top10m: [0, 0],
        replace_values: ["llr", [-20, 20], ["-20", "20"]],
      } as Config,
      config_1: {
        model: "icann",
        wsize: 500,
        windowing: "both",
        top10m: [0, 0],
        replace_values: ["llr", [-20, 20], ["-20", "20"]],
      } as Config,
      hash_0: null,
      hash_1: null,
      cms_0: {} as CMS,
      cms_1: {} as CMS,
      ths_measures: {},
      convert_lambda: {
        0: 0,
        1: 1,
        "-6.906754778648554": "λ(0.001)",
        2.1972245773362196: "λ(0.9)",
        6.906754778648553: "λ(0.999)",
        13.815509557935018: "λ(0.999999)",
      },
    };
  },
  async mounted() {
    await this.all_configs_fetch();
  },
  computed: {
    integrals0() {
      if (!this.cms_0.ths) {
        return {};
      }

      const int = [0, 0, 0];
      for (let i = 0; i < this.cms_0.ths.length; ++i) {
        for (let dga = 0; dga < 3; ++dga) {
          int[dga] +=
            this.cms_0.cms.tn[i] < this.cms_0.cms.tp[dga][i]
              ? this.cms_0.cms.tn[i]
              : this.cms_0.cms.tp[dga][i];
        }
      }

      return int;
    },
    integrals1() {
      if (!this.cms_1.ths) {
        return {};
      }

      const int = [0, 0, 0];
      for (let i = 0; i < this.cms_1.ths.length; ++i) {
        for (let dga = 0; dga < 3; ++dga) {
          int[dga] +=
            this.cms_1.cms.tn[i] < this.cms_1.cms.tp[dga][i]
              ? this.cms_1.cms.tn[i]
              : this.cms_1.cms.tp[dga][i];
        }
      }

      return int;
    },
  },
  methods: {
    // all_configs_changed() {
    //   if (Object.keys(this.all_configs).length === 0) return;

    //   this.all_configs_checked = Object.keys(this.all_configs).reduce((aps, hash) => {
    //     const ap = this.all_configs[hash];
    //     ap.hash = hash;
    //     if (ap.checked) aps.push(ap);
    //     return aps;
    //   }, []);
    // },
    async all_configs_fetch() {
      this.all_configs = (
        await axios.get("http://127.0.0.1:3000/mwdb/configs")
      ).data.all_configs;
    },
  },
  watch: {
    config_0: {
      async handler(newConfig: Config) {
        const current_rv_type = newConfig.replace_values[0];

        if (rv_type(newConfig) !== current_rv_type) {
          this.config_0.replace_values = this.all_configs.replace_values.filter(
            (rv) => rv[0] === (newConfig.model === "nx" ? "nx" : "llr")
          )[1];
        }

        this.hash_0 = (
          await axios.post("http://127.0.0.1:3000/mwdb/configs/hash", {
            config: newConfig,
          })
        ).data.hash;

        this.cms_0 = (
          await axios.post("http://127.0.0.1:3000/mwdb/cms", {
            hash: this.hash_0,
          })
        ).data;

        plot_scatter("plot_1", this.cms_0.ths, this.cms_0.cms, this.cms_1.cms);
      },
      deep: true,
    },
    config_1: {
      async handler(newConfig: Config) {
        const current_rv_type = newConfig.replace_values[0];

        if (rv_type(newConfig) !== current_rv_type) {
          newConfig.replace_values = this.all_configs.replace_values.filter(
            (rv) => rv[0] === (newConfig.model === "nx" ? "nx" : "llr")
          )[1];
        }

        this.hash_1 = (
          await axios.post("http://127.0.0.1:3000/mwdb/configs/hash", {
            config: newConfig,
          })
        ).data.hash;

        this.cms_1 = (
          await axios.post("http://127.0.0.1:3000/mwdb/cms", {
            hash: this.hash_1,
          })
        ).data;

        plot_scatter("plot_1", this.cms_0.ths, this.cms_0.cms, this.cms_1.cms);
      },
      deep: true,
    },
  },
});
</script>

<template>
  <div class="configs">
    <table v-if="all_configs.models !== undefined" class="center">
      <thead>
        <tr>
          <th>model</th>
          <th>wsize</th>
          <th>top10m</th>
          <th>windowing</th>
          <th>replace value</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(config, index) in [config_0, config_1]"
          :key="`comparer_${index}`"
        >
          <td>
            <div class="row">
              <select v-model="config.model">
                <option
                  v-for="model in all_configs.models"
                  :key="`select_wsize_${index}_${model}`"
                  :value="model"
                >
                  {{ model }}
                </option>
              </select>
            </div>
          </td>
          <td>
            <div class="row">
              <select v-model.number="config.wsize">
                <option
                  v-for="_wsize_ in all_configs.wsize"
                  :key="`select_wsize_${index}_${_wsize_}`"
                  :value="_wsize_"
                >
                  {{ _wsize_ }}
                </option>
              </select>
            </div>
          </td>
          <td>
            <div class="row">
              <select v-model="config.top10m">
                <option
                  v-for="_top10m_ in all_configs.top10m"
                  :key="`select_top10m_${index}_${_top10m_}`"
                  :value="_top10m_"
                >
                  {{ _top10m_[0] }}, {{ _top10m_[1] }}
                </option>
              </select>
            </div>
          </td>
          <td>
            <div class="row">
              <select v-model="config.windowing">
                <option
                  v-for="_windowing_ in all_configs.windowing"
                  :key="`select_windowing_${index}_${_windowing_}`"
                  :value="_windowing_"
                >
                  {{ _windowing_ }}
                </option>
              </select>
            </div>
          </td>
          <td>
            <div class="row">
              <select v-model="config.replace_values">
                <option
                  v-for="(_rp_, i) in all_configs.replace_values"
                  :key="`select_rp_${index}_llr_${i}`"
                  :value="_rp_"
                  :disabled="(config.model === 'nx' ? 'nx' : 'llr') !== _rp_[0]"
                >
                  {{ _rp_[2][0] }},
                  {{ _rp_[2][1] }}
                </option>
              </select>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    <div class="plots">
      <div id="plot_1"></div>
    </div>
    {{ integrals0 }}
    <br/>
    {{ integrals1 }}
  </div>
</template>

<style scoped>
.plots {
  display: flex;
  flex-direction: row;
  width: 100%;
}
.plots > div {
  width: 40%;
}
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
#app > div.configs > table > tbody {
  text-align: left;
}
table > tbody > tr > td,
th {
  text-align: left;
}
</style>
