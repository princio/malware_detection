
<template>
  <div id="apply-bar">
    <table class="center">
      <tbody>
        <tr>
          <td>
            threshold:
            <div class="row">
              <input
                type="range"
                :min="bounds.min"
                :max="bounds.max"
                step=1
                v-on:change="emit_fields"
                v-model.number="fields.th"
              />
              <input type="text" style="width:50px"
                v-on:change="emit_fields"
                v-model.number="fields.th"
              />
            </div>
          </td>
          <td>
            campionamento:
            <div class="row">
              <input
                type="range"
                :min="10"
                :max="500"
                :step="10"
                v-on:change="emit_fields"
                v-model.number="fields.sampling"
              />
              <input type="text" style="width:50px"
                v-on:change="emit_fields"
                v-model.number="fields.sampling"
              />
            </div>
          </td>
          <td>
            <div class="row checkbox-button">
                <label>
                  <input type="checkbox"
                    v-model="fields.tp"
                  />
                  <span>TP</span>
                </label>
                <label>
                  <input type="checkbox"
                    v-model="fields.tn"
                  />
                  <span>TN</span>
                </label>
            </div>
          </td>
          <td>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  name: "ApplyPlotBar",
  props: [ 'applies', 'mounted' ],
  data: function(){
    this.bounds = { min: -100, max: 100 };
    return {
      fields: {
        th: 50,
        tp: true,
        tn: true,
        sampling: 100,
      },
    }
  },
  async mounted() {
    this.fields.dgas['all'] = true;
  },
  methods: {
    set_bounds() {
      let max = 0;
      let min = 0;

      for (const apply of this.applies) {
        if (this.fields.applies[apply.id]) {
          if (max < apply.max) max = apply.max;
          if (min > apply.min) min = apply.min;
        }
      }

      this.bounds.max = 100000;
      this.bounds.min = -100000;
    },
    change_dga() {
      this.emit_fields();
    },
    emit_fields() {
      this.$emit('update:fields', this.fields)
    }
  },
  watch: {
    'applies': {
      handler(applies) {
        let first = true;
        
        for (const hash in applies) {
          const apply = this.applies[hash];
          this.$set(this.fields.applies, apply.id, first)
          first = false;
          this.bounds[apply.id] = {
            max: applies.max,
            min: applies.min
          };
        }
        this.emit_fields();
      }
    },
    'mounted': {
      handler() {
        this.emit_fields();
      }
    }
  }
};
</script>

<style .scoped>
.active {
  background-color: lightskyblue;
}
</style>