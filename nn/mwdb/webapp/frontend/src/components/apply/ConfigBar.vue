<template>
  <div class="configs">
    <table class="center">
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
        <tr v-for="(config, index) in [ config_0,  config_1 ]" :key="`comparer_${index}`">
          <td>
            <div class="row">
              <select
                v-model="config.model">
                <option v-for="model in all_configs.models" :key="`select_wsize_${index}_${model}`" :value="model">
                  {{ model }}
                </option>
              </select>
            </div>
          </td>
          <td>
            <div class="row">
              <select
                v-model.number="config.wsize">
                <option v-for="_wsize_ in all_configs.wsize" :key="`select_wsize_${index}_${_wsize_}`" :value="_wsize_">
                  {{ _wsize_ }}
                </option>
              </select>
            </div>
          </td>
          <td>
            <div class="row">
              <select
                v-model="config.top10m">
                <option v-for="_top10m_ in all_configs.top10m" :key="`select_top10m_${index}_${_top10m_}`" :value="_top10m_">
                  {{ _top10m_[0] }}, {{ _top10m_[1] }}
                </option>
              </select>
            </div>
          </td>
          <td>
            <div class="row">
              <select
                v-model="config.windowing">
                <option v-for="_windowing_ in all_configs.windowing" :key="`select_windowing_${index}_${_windowing_}`" :value="_windowing_">
                  {{ _windowing_ }}
                </option>
              </select>
            </div>
          </td>
          <td>
            <div class="row">
              <select v-if="config.model !== 'nx'"
                v-model="config.replace_value">
                <option v-for="(_rp_, i) in all_configs.replace_values.llr" :key="`select_rp_${index}_llr_${i}`" :value="_rp_">
                  {{ _rp_[0] }}, 
                  {{ _rp_[1] }}
                </option>
              </select>
              <select v-else
                v-model="config.replace_value">
                <option v-for="(_rp_, i) in all_configs.replace_values.nx" :key="`select_rp_${index}_nx_${i}`" :value="_rp_">
                  {{ convert_lambda[_rp_[0]] }}, 
                  {{ convert_lambda[_rp_[1]] }}
                </option>
              </select>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    {{ hash_0 }}
    <br/>
    {{ hash_1 }}
  </div>
</template>

<script>
const axios = require("axios");

export default {
  name: "ConfigBar",
  data: function () {
    this.ths_measures = {};
    this.convert_lambda = {
      0: 0,
      1: 1,
      '-6.906754778648554': 'λ(0.001)',
      2.1972245773362196: 'λ(0.9)',
      6.906754778648553: 'λ(0.999)',
      13.815509557935018: 'λ(0.999999)'
    }
    return {
      all_configs: {},
      config_0: {
            model: 'icann',
            wsize: 500,
            windowing: 'both',
            top10m: [ 0, 0 ],
            replace_value: [ -20, 20 ]
      },
      config_1: {
          model: 'nx',
          wsize: 500,
          windowing: 'both',
          top10m: [ 0, 0 ],
          replace_value: [ 0, 1 ]
      },
      hash_0: null,
      hash_1: null,
    };
  },
  async mounted() {
    await this.all_configs_fetch();
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
      async handler(newConfig) {
        if (newConfig.replace_value === undefined) {
          console.log(this.all_configs.replace_values[newConfig.models === 'nx' ? 'nx' : 'llr']);
          newConfig.replace_value = this.all_configs.replace_values[newConfig.models === 'nx' ? 'nx' : 'llr'][0];
        }
        this.hash_0 = (
          await axios.post("http://127.0.0.1:3000/mwdb/configs/hash", {
            config: newConfig
          })
        ).data.config_chosen;
        const cms = (
          await axios.post("http://127.0.0.1:3000/mwdb/cms", {
            hash: this.hash_0
          })
        ).data;
        console.log(cms);
      },
      deep: true
    },
    config_1: {
      async handler(newConfig) {
        console.log('ciaooooooooo');
        if (newConfig.replace_value === undefined) {
          newConfig.replace_value = this.all_configs.replace_values[newConfig.models === 'nx' ? 'nx' : 'llr'][0];
        }
        this.hash_1 = (
          await axios.post("http://127.0.0.1:3000/mwdb/configs/hash", {
            config: newConfig
          })
        ).data.config_chosen;

        console.log(this.hash_1);

        const cms = (
          await axios.post("http://127.0.0.1:3000/mwdb/cms", {
            hash: this.hash_1
          })
        ).data;

        console.log(cms);
      },
      deep: true
    }

  }
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
#app > div.configs > table > tbody {
  text-align: left;
}
table > tbody > tr > td,
th {
  text-align: left;
}
</style>