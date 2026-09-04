import * as Plotly from "plotly.js/lib/core";
import * as Scatter from "plotly.js/lib/scatter";
import createPlotlyComponent from "react-plotly.js/factory";

Plotly.register(Scatter);

export const Plot = createPlotlyComponent(Plotly);
