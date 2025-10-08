import './style.css';
import * as d3 from 'd3';
import * as topojson from 'topojson-client';

const width = 800;
const height = 600;

const app = d3.select<HTMLDivElement, unknown>('#app');

const map = app.append("svg")
  .attr("id", "map")
  .attr("width", width)
  .attr("height", height);

const g = map.append("g");

const tooltip = app.append("div")
  .attr("id", "tooltip")
  .attr("class", "tooltip");

const projection = d3.geoMercator();
const path = d3.geoPath().projection(projection);

let active = d3.select(null);

d3.json("florida.json").then((topo) => {
  const counties = topojson.feature(topo, topo.objects["florida-counties"]);

  projection.fitSize([width, height], counties);

  g
    .selectAll('path')
    .data(counties.features)
    .enter()
    .append('path')
    .attr('class', 'county')
    .attr('d', path)
    .on('mouseover', (event, d) => {
      tooltip
        .style('opacity', 1)
        .html(d.properties.county)
        .style('left', event.pageX + 10 + 'px')
        .style('top', event.pageY - 15 + 'px');
    })
    .on('mousemove', (event) => {
      tooltip
        .style('left', event.pageX + 10 + 'px')
        .style('top', event.pageY - 15 + 'px');
    })
    .on('mouseout', () => {
      tooltip.style('opacity', 0);
    })
    .on('click', clicked);
});

function clicked(event: MouseEvent, d: any) {
  if (active.node() === this) return reset();

  active.classed("active", false);
  active = d3.select(this).classed("active", true);

  event.stopPropagation();
  const bounds = path.bounds(d);
  const dx = bounds[1][0] - bounds[0][0];
  const dy = bounds[1][1] - bounds[0][1];
  const x = (bounds[0][0] + bounds[1][0]) / 2;
  const y = (bounds[0][1] + bounds[1][1]) / 2;

  const scale = Math.max(1, Math.min(8, 0.9 / Math.max(dx / width, dy / height)));
  const translate = [width / 2 - scale * x, height / 2 - scale * y];

  g.transition()
    .duration(750)
    .attr("transform", `translate(${translate})scale(${scale})`);
}

function reset() {
  active.classed("active", false);
  active = d3.select(null);

  g.transition()
    .duration(750)
    .attr("transform", "");
}

map.on("click", reset);
