<template>
  <div class="pcaps">
    <h1>PcapsS</h1>


    <table
    class="center"
      ref="pcaps_table">
      <thead>
        <tr >
          <th style='width: 60px;' v-for="(h, hindex) in df.columns" :key="`header_${hindex}`">
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
      <tbody ref="pcaps_table_body">
        <tr v-for="(row, rindex) in df.values" :key="`row_${rindex}`">
          <td v-for="(v, cindex) in row" :key="`cell_index_${rindex}_${cindex}`">
            <span :class="row[df.columns.indexOf('infected')] ? 'infected' : 'normal'">{{ v }}</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
//const axios = require('axios');
const dfd = require('danfojs/dist/index')

export default {
  name: 'Pcaps',
  components: {
  },
  data: function () {
    this.ths_measures = {};
    return {
      header: {},
      values: [],
      df: new dfd.DataFrame()
    };
  },
  async created() {

    this.df = (await dfd.read_json('http://127.0.0.1:3000/mwdb/pcap/json'))
      .drop({ columns: 'hash' });
  },
  methods: {
    setHSort(hindex, asc) {
      this.df = this.df.sort_values({ by: this.df.columns[hindex], ascending: asc })
    }
  }
}
</script>


<style scoped>
.infected {
  color: red;
}
.center {
  text-align: center;
  margin: auto;
}
#app > div.pcaps > table > tbody {
  text-align: left;
  white-space: nowrap;
}
#app > div.pcaps > table > tbody td {
  padding: 5px 10px;
}
</style>