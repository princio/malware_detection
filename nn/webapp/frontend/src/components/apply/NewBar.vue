
<template>
  <div id="apply-bar">
    <table class="center">
      <tbody>
        <tr>
          <td>
            model:
            <div class="row">
              <select
                v-model.number="model_id">
                <option v-for="model in models" :key="`select_wsize_${model.name}`" :value="model.id">
                  {{ model.name }}
                </option>
              </select>
            </div>
          </td>
          <td>
            wsize:
            <div class="row">
              <select
                v-model.number="wsize">
                <option v-for="_wsize_ in [ 100, 500, 2500 ]" :key="`select_wsize_${_wsize_}`" :value="_wsize_">
                  {{ _wsize_ }}
                </option>
              </select>
            </div>
          </td>
          <td>
            top10m:
            <div class="row">
              <input
                type='number'
                min="0"
                max="9999645"
                step="1"
                v-model.number="top10m"
              />
            </div>
          </td>
          <td>
            windowing:
            <div class="column">
                <div
                v-for="_windowing_ in [ 'req', 'res', 'both' ]" :key="`div_windowing_${_windowing_}`">
                <input type="radio"
                  :name="`name_radio_${_windowing_}`"
                  :value="_windowing_"
                  v-model="windowing" 
                  />
                <label :for="`name_radio_${_windowing_}`">{{ _windowing_ }}</label>
                </div>
            </div>
          </td>
          <td>
            wtype:
            <div class="column">
                <div
                v-for="_wtype_ in [ 'llr', 'nx' ]" :key="`div_wtype_${_wtype_}`">
                <input type="radio"
                  :name="`name_radio_${_wtype_}`"
                  :value="_wtype_"
                  v-model="wtype" 
                  />
                <label :for="`name_radio_${_wtype_}`">{{ _wtype_ }}</label>
                </div>
            </div>
          </td>
          <td v-if="wtype == 'llr'">
            ninf:
            <div class="row">
              <input
                type='number'
                step="1"
                style="width: 50px"
                v-on:change="check_infs()"
                v-model.number="ninf"
              />
            </div>
          </td>
          <td v-if="wtype == 'llr'">
            pinf:
            <div class="row">
              <input
                type='number'
                step="1"
                style="width: 50px"
                v-on:change="check_infs()"
                v-model.number="pinf"
              />
            </div>
          </td>
          <td>
            description:
            <div class="row">
              <input
                type="text"
                v-model="description"
              />
            </div>
          </td>
          <td>
            <button v-on:click="apply_new()" :disabled="loading">New</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import axios from 'axios';
export default {
  name: "ApplyNewBar",
  props: [ 'mounted' ],
  data: function() {
    return {
      hash: '',
      description: "prova",
      model_id: 0,
      models: [],
      top10m: 0,
      windowing: "req",
      wsize: 2500,
      wtype: "llr",
      ninf: -100,
      pinf: 100,
      loading: false
    }
  },
  async mounted() {
    this.models = (await axios.get('http://127.0.0.1:3000/mwdb/model/fetch')).data.models
    this.model_id = 1;
  },
  methods: {
    async apply_new() {
      this.loading = true;
      axios.post(
        'http://127.0.0.1:3000/mwdb/apply/do', {
          name: this.description,
          model_id: this.model_id,
          wtype: this.wtype,
          top10m: this.top10m,
          wsize: this.wsize,
          windowing: this.windowing,
          pinf: this.pinf,
          ninf: this.ninf
      }).then((res) => {
        console.log(res);
        this.hash = res.data.hash;
        this.emit_fields();
        this.loading = false;
        this.$nextTick();
      })
      .catch(() => {
        this.loading = false;
        this.$nextTick();
      })
    },
    check_infs() {
      if (this.pinf < this.ninf) {
        this.pinf = 100;
        this.ninf = -100
      }
    },
    emit_fields() {
      this.$emit('update:hash')
    }
  }
};
</script>

<style .scoped>
.active {
  background-color: lightskyblue;
}
table > tbody > tr > td {
  text-align: left !important;
}
</style>