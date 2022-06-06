
const d3 = require('d3');
// const { colourNameToHex } = require('./colors.js');


function get_fields() {
    const f = {
        type: Object,
        default: function () {
            return {
                applies: {},
                dgas: {},
                sampling: 100,
                th: 50,
            }
        }
    };
    return f;
}


const vdga_colors = {
    all: 'brown',
    1: 'burlywood',
    2: 'coral',
    3: 'crimson'
};

const cm_template = { tn: 0, fp: 0, fn: 0, tp: 0 };

const get_cms = function (dfs, ths) {
    const cms = [];
    const apply_ids = Object.keys(dfs);
    const dgas = [ 'all', 1, 2, 3 ];

    const cm_empty = { th: 0, ...Object.fromEntries(
        apply_ids.map((a) => [
            a,
            Object.fromEntries(dgas.map((d) => [ d, {...cm_template} ]))
        ]
    ))};

    for (const th of ths) {

        let cm = JSON.parse(JSON.stringify(cm_empty));

        for (const a of apply_ids) {

            const v_wcount = dfs[a]['wcount'].values;
            const v_wvalue = dfs[a]['wvalue'].values;
            const v_dga = dfs[a]['dga'].values;

            cm.th = th;

            for (let j = 0; j < v_dga.length; j++) {
                let dgas_tofill;
                let measures_tofill;
                const infected = (v_wvalue[j] > th);

                if (v_dga[j] === 0) {
                    dgas_tofill = dgas;
                    measures_tofill = infected ? 'fp' : 'tn';
                }
                else {
                    dgas_tofill = [ 'all', v_dga[j] ];
                    measures_tofill = infected ? 'tp' : 'fn';
                }

                for(const dga_tofill of dgas_tofill) {
                    cm[a][dga_tofill][measures_tofill] +=  v_wcount[j]
                }
            }
        }

        cms.push(cm);
    }

    return cms;
}

const get_dgas = function(dga1, dga2, dga3) {
    return {
        1: dga1,
        2: dga2,
        3: dga3
    }
}

const get_ths = function(max, min, sampling) {
    const step = +((max - min) / sampling).toPrecision(2);

    const ths = [];

    for (let i = min; i <= max; i += step) {
        ths.push(Number(i));
    }

    return ths;
}

// const get_cms = function(df, ths) {
//     return ths.map(th => get_cm(df, th));
// }

const calculate_plot = function (cms, relative=true) {

    const x = [];
    const y_n = [];
    const y_p = [];

    let p = 1;
    let n = 1;
    if (relative) {
        const tmp = cms[Object.keys(cms)[0]].cm;
        p = tmp.tp + tmp.fn;
        n = tmp.tn + tmp.fp;
    }

    for (const cm of cms) {
        x.push(cm.th);
        y_n.push(+(cm.cm.fp/n).toPrecision(2));
        y_p.push(+(cm.cm.tp/p).toPrecision(2));
    }

    return { x, y_n, y_p };
};

const report = function (cm) {

    const { tn, fp, fn, tp } = cm;

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
        f1: (normal.f1 + infected.f1) / 2,
        accuracy: (tp + tn) / (tp + tn + fp + fn)
    }

    return {
        normal,
        infected,
        macro
    }
};

const generate_frame = function (apply, visual_cm, fields) {

    const f = d3.format('.2s');

    const dgas_str = Object.keys(fields.dgas).map((dd) => fields.dgas[dd] ? dd : '').join('');

    const fn = `plot_${apply.wtype}_${apply.windowing}_${apply.wsize}_${f(apply.top10m)}_${dgas_str}_th${f(fields.th).replace('−', '-')}_${visual_cm.tp}_${visual_cm.tn}`;

    const frame = `
          
    \\begin{frame}{ww=${apply.windowing}, s=${apply.wsize}, vDGA=${dgas_str}, $t^*$=\\numprint{${apply.top10m}}}
    
        \\begin{align*}
            &th = ${f(fields.th).replace('−', '-')} \\\\
            &\\begin{pmatrix}
                    ${visual_cm.tn} & ${visual_cm.fp} \\\\
                    ${visual_cm.fn} & ${visual_cm.tp} \\\\
                \\end{pmatrix}
        \\end{align*}
        \\begin{center}
            \\includegraphics[trim={2cm 0 0 3.5cm},clip, width=\\textwidth]{plots/${fn}.jpeg}
        \\end{center}
    
    \\end{frame}
    `;

    return { frame, fn };
};

const copy2clipboard = function (document, tocopy) {
    let textArea = document.createElement("textarea");
    textArea.value = tocopy;
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
}

const get_plotly = function (plot, th) {

    var trace1 = {
        x: plot.x,
        y: plot.y_n,
        type: 'scatter',
        name: 'tnr'
    };

    var trace2 = {
        x: plot.x,
        y: plot.y_p,
        type: 'scatter',
        name: 'tpr'
    };

    var data = [trace1, trace2];

    const { annotation, shape } = get_plotly_annotations_for_th(th);

    return {
        data,
        layout: {
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
                range: [-0.1, 1.1]
            },
            annotations: [
                annotation
            ],
            shapes: [
                shape
            ]
        },
        // options: {
        //     modeBarButtonsToAdd: [
        //         {
        //             name: 'download&copy',
        //             icon: Plotly.Icons.pencil,
        //             click: (gd) => {
        //                 const { frame, fn } = generate_frame(apply, visual_cm, th, dgas);
        //                 copy2clipboard(document, frame);
        //                 Plotly.downloadImage(gd, {
        //                     filename: fn,
        //                     format: 'jpeg',
        //                     width: gd._fullLayout.width,
        //                     height: gd._fullLayout.height
        //                 });
        //             }
        //         },
        //     ],
        // }
    };
}

const cm_relative = function(cm) {
    const cmr = {};
    for (const k in cm) {
        cmr[k] = {
            tp: (cm[k].tp / (cm[k].tp+cm[k].fn)).toFixed(2),
            tn: (cm[k].tn / (cm[k].tn+cm[k].fp)).toFixed(2),
            fp: (cm[k].fp / (cm[k].tn+cm[k].fp)).toFixed(2),
            fn: (cm[k].fn / (cm[k].tp+cm[k].fn)).toFixed(2),
        }
    }
    return cmr;
}


const get_plotly2 = function (cms, ths, th, applies, fields, thrange = 0.75, relative = true) {

    console.log('get_plotly2', fields);

    // if (comparer.dgas.length > 1) {
    //     if (comparer.applies.length > 1) {
    //         throw 'If comparision is between two or more DGAs then only ONE APPLY can be selected.';
    //     }
    // }

    function _cm(i, apply_id, dga) {
        return cms[i][apply_id][dga];
    }

    const plots = [];
    const n = _cm(0, 0, 1).tn + _cm(0, 0, 1).fp;
    for (const apply_id in applies) {
        for (const dga in applies[apply_id].dgas) {
            if (applies[apply_id].dgas[dga]) {
                plots.push({
                    apply_id,
                    dga,
                    label: `${apply_id}_${dga}`,
                    y: { tn: [], tp: [], plus: [] },
                    n,
                    p: _cm(0, apply_id, dga).fn + _cm(0, apply_id, dga).tp,
                    thr: { begin: undefined, end: undefined },
                    color: applies[apply_id].color,
                    apply: applies[apply_id]
                });
            }
        }
    }

    const x = [];
    for (const i in cms) {
        const cm = cms[i];
        
        x.push(ths[i]);
        for (const plot of plots) {
            let n_den = relative ? plot.n : 1;
            let p_den = relative ? plot.p : 1;
            const tn = cm[plot.apply_id][plot.dga].tn/n_den;
            const tp = cm[plot.apply_id][plot.dga].tp/p_den;
            plot.y.tn.push(+(tn).toPrecision(2))
            plot.y.tp.push(+(tp).toPrecision(2))
            plot.y.plus.push(+(tp+tn).toPrecision(2))

            if (undefined === plot.thr.begin && (tn >= thrange && tp >= thrange)) {
                plot.thr.begin = ths[i];
            } else
            if (undefined === plot.thr.end && !(tn >= thrange && tp >= thrange) && th > plot.thr.begin) {
                plot.thr.end = ths[i];
            }
        }
    }


    const data = [];

    // var trace_fp = {
    //     x: x,
    //     y: y.all.fp,
    //     type: 'scatter',
    //     name: `FP`,
    //     line: {
    //         color: 'black',
    //         dash: 'solid'
    //     }
    // };

    // data.push(trace_fp);

    // const colors = {
    //     all: colourNameToHex('darkgreen'), // brown
    //     1: colourNameToHex('burlywood'),
    //     2: colourNameToHex('coral'),
    //     3: colourNameToHex('crimson') //crimson
    // };

    // const colors2 = Object.values(colors);

    // const dash = {
    //     all: 'solid',
    //     1: 'solid',
    //     2: 'solid',
    //     3: 'solid'
    // };

    const thrs = [];

    for (const plot of plots) {
        // let color;
        // if (dgas.length > 1 || applies.length === 1) {
        //     color = colors[plot.dga];
        // } else {
        //     color = plot.apply.color; // colors2[plots.indexOf(plot)];
        // }
        // color = plot.apply.color;

        const color = plot.apply.color;

        const name = `${plot.apply.name} ${plot.dga}`

        if (fields.tp) {
            var trace_tp = {
                x: x,
                y: plot.y.tp,
                type: 'scatter',
                name: `TP ${name}`,
                line: {
                    color,
                    // dash: dash[k],
                    size: '1px'
                }
            }
            data.push(trace_tp);
        }

        if (fields.tn) {
            var trace_fp = {
                x: x,
                y: plot.y.tn,
                type: 'scatter',
                name: `TN ${name}`,
                line: {
                    color,
                    dash: 'dot',
                    size: '1px'
                }
            }
            data.push(trace_fp);
        }

        if (plot.thr.begin) {
            thrs.push({
                type: 'rect',
                x0: plot.thr.begin,
                y0: 0,
                x1: plot.thr.end,
                y1: 0.75,
                line: {
                    color: color,
                    width: 2,
                    dash: 'solid'
                },
                fillcolor: color + '33',
            });
        }
    }

    const { annotation, shape } = get_plotly_annotations_for_th(th);

    thrs.push(shape);

    return {
        data,
        layout: {
            autosize: false,
            // plot_bgcolor: 'lightgray',
            title: {'text': undefined},
            width: 1000,
            height: 600,
            margins: { l: 10, r: 10, t: 0, b: 10 },
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
                range: [-0.1, 1.1]
            },
            annotations: [
                annotation
            ],
            shapes: thrs
        },
    };
}

const get_plotly_annotations_for_th = function (th) {

    const f = d3.format('.2s');

    const annotation = {
        text: 'th=' + f(th),
        x: th,
        y: 1.05,
        align: 'right',
        xanchor: 'left',
        showarrow: false
    }

    const shape = {
        type: 'line',
        x0: th,
        y0: 0,
        x1: th,
        y1: 1,
        line: {
            color: 'grey',
            width: 1.5,
            dash: 'dash'
        }
    };

    return { annotation, shape };
}

export {
    get_fields,
    vdga_colors,
    // get_cm,
    get_ths,
    get_cms,
    get_dgas,
    cm_relative,
    calculate_plot,
    report,
    generate_frame,
    copy2clipboard,
    get_plotly,
    get_plotly2,
    get_plotly_annotations_for_th
}