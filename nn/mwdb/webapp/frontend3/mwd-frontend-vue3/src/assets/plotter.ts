import * as d3 from 'd3';

interface Datum001 {
  name: string;
  type: 0|1;
  values: [number, number][];
}

const plot_scatter =
    function(
        div_id: string, ths: number[],
        cms0: {tn: number[], tp: [number[], number[], number[]]},
        cms1: {tn: number[], tp: [number[], number[], number[]]}) {
  d3.select(`#${div_id}`).select('svg').remove();

  const margin = {top: 10, right: 100, bottom: 30, left: 30},
        width = 2 * (460 - margin.left - margin.right),
        height = 400 - margin.top - margin.bottom;

  const svg =
      d3.select<SVGGElement, Datum001>(`#${div_id}`)
          .append('svg')
          .attr('width', width + margin.left + margin.right)
          .attr('height', height + margin.top + margin.bottom)
          .append('g')
          .attr(
              'transform', 'translate(' + margin.left + ',' + margin.top + ')');

  var clip = svg.append('defs')
                 .append('svg:clipPath')
                 .attr('id', 'clip')
                 .append('svg:rect')
                 .attr('width', width)
                 .attr('height', height)
                 .attr('x', 0)
                 .attr('y', 0);

  var area = svg.append('g').attr('clip-path', 'url(#clip)')

  const dgas = ['dga_0', 'dga_1', 'dga_2'];

  const myColor =
      d3.scaleOrdinal().domain(dgas).range(['blue', 'orange', 'red']);

  let data = [{}] as Datum001[];
  let data2 = [{}] as Datum001[];
  let data_indexs = {};

  if (cms0 !== undefined) {
    data = dgas.map((dga, index_dga) => ({
                      name: dga,
                      type: 0,
                      values: ths.map((th, index) => ([
                                        index, cms0.tp[index_dga][index]
                                      ] as [number, number]))
                    }));
  }
  if (cms1 !== undefined) {
    data2 = dgas.map((dga, index_dga) => ({
                       name: dga,
                       type: 1,
                       values: ths.map((th, index) => ([
                                         index, cms1.tp[index_dga][index]
                                       ] as [number, number]))
                     }));
    data = [...data, ...data2];
  }

  // let data = [] as [number, number][];
  // let data_indexes = [] as {name: string, dga: string, cms: number}[];

  // if (cms0 !== undefined) {
  //   dgas.forEach((dga, index_dga) => {
  //     data_indexes.push({ name: dga, cms: 0, dga });
  //     data = [ ...data, ...ths.map((th, index) => ([index,
  //     cms0.tp[index_dga][index]] as [number, number]))];
  //   });
  // }
  // if (cms1 !== undefined) {
  //   dgas.forEach((dga, index_dga) => {
  //     data_indexes.push({ name: dga, cms: 1, dga });
  //     data = [ ...data, ...ths.map((th, index) => ([index,
  //     cms1.tp[index_dga][index]] as [number, number]))];
  //   });
  // }

  // const x = d3.scaleLinear().domain([ths[0], ths[ths.length - 1]]).range([0,
  // width]);
  const x = d3.scaleLinear().domain([0, 200]).range([0, width]);

  const xSVG = svg.append('g')
                   .attr('transform', 'translate(0,' + height + ')')
                   .call(d3.axisBottom(x));

  const y = d3.scaleLinear().domain([0, 1.02]).range([height, 0]);

  svg.append('g').call(d3.axisLeft(y));

  const areaGenerator = d3.area().x((d) => x(d[0])).y0(y(0)).y1((d) => y(d[1]));

  const line = d3.line().x((d) => x(d[0])).y((d) => y(d[1]));

  area.selectAll('myLines')
      .data(data)
      .enter()
      .append('path')
      .attr('class', 'myArea')
      .attr('d', (d) => line(d.values))
      .attr('fill-opacity', .0)
      // .attr("fill", "#69b3a2")
      // .attr('d', (d) => areaGenerator(d.values))
      .attr('stroke', (d) => myColor(d.name) as string)
      .style('stroke-width', 1)
      .style('stroke-dasharray', (d, i) => [('0, 0'), ('3, 3')][d.type]);

  const x_pos = [
    (width) * 0.4,
    (width) * 0.6
  ];

  area.selectAll('myLegends')
      .data(data)
      .enter()
      .append('text')
      .attr('class', 'myLegend')
      .attr('x', d => x_pos[d.type])
      .attr('y', (d) => y(d.values[Math.floor(x.invert(x_pos[d.type]))][1]))
      .style('fill', (d) => myColor(d.name) as string)
      .text((d) => `${d.name}/${d.type}`)
      .attr('text-anchor', 'center')
      .style('font-size', '10px');

  // BRUSH ////////////////////////

  var brush = d3.brushX<Datum001>()
                  .extent([[0, 0], [width, height]])
                  .on('end', updateChart);

  area.append('g').attr('class', 'brush').call(brush);


  var idleTimeout: number|null;
  function idled() {
    idleTimeout = null;
  }

  function updateChart(_event: any) {
    const extent = _event.selection

    if (!extent) {
      if (!idleTimeout) return idleTimeout = setTimeout(idled, 350);
      x.domain([4, 8])
    }
    else {
      x.domain([x.invert(extent[0]), x.invert(extent[1])]);
      svg.select<SVGGElement>('.brush').call(brush.move, null);
    }

    xSVG.transition().duration(1000).call(d3.axisBottom(x))

    area.selectAll<SVGPathElement, Datum001>('.myArea')
        .transition()
        .duration(1000)
        .attr('d', (d) => line(d.values));

    if (extent) {
      
      const x_pos = [
        x.range()[0] + (x.range()[1] - x.range()[0]) * 0.4,
        x.range()[0] + (x.range()[1] - x.range()[0]) * 0.6
      ];

      area.selectAll<SVGTextElement, Datum001>('.myLegend')
          .transition()
          .duration(1000)
          .attr('x', d => x_pos[d.type])
          .attr('y', d => y(d.values[Math.floor(x.invert(x_pos[d.type]))][1]));
    }
  }

  svg.on('dblclick', () => {
    x.domain([0, 200]);

    xSVG.transition().call(d3.axisBottom(x));

    area.selectAll<SVGPathElement, Datum001>('.myArea')
        .transition()
        .duration(200)
        .attr('d', (d) => line(d.values));
      
    const x_pos = [
      x.range()[0] + (x.range()[1] - x.range()[0]) * 0.4,
      x.range()[0] + (x.range()[1] - x.range()[0]) * 0.6
    ]

    area.selectAll<SVGTextElement, Datum001>('.myLegend')
        .transition()
        .duration(200)
        .attr('x', d => x_pos[d.type])
        .attr('y', (d) => y(d.values[Math.floor(x.invert(x_pos[d.type]))][1]));
  });

  // BRUSH ////////////////////////

  return;
}

export {plot_scatter};