import './style.css';
import * as d3 from 'd3';
import * as topojson from 'topojson-client';


const width = 800;
const height = 600;
// Select the div with the ID 'app'
// This is the most likely point of failure.
const app = d3.select<HTMLDivElement, unknown>('#app');

const map = app.append("svg")
  .attr("id", "map")
  .attr("width", width)
  .attr("height", height);

const tooltip = app.append("div")
  .attr("id", "tooltip")
  .attr("class", "tooltip");


const projection = d3.geoMercator()
  .fitSize([width, height], {
    type: "FeatureCollection",
    features: []
  });

const path = d3.geoPath().projection(projection);

d3.json("florida.json").then((topo) => {
  const counties = topojson.feature(topo, topo.objects["florida-counties"])
  projection.fitSize([width, height], counties);
  map
    .append('g')
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
        .style('left', event.pageX + 5 + 'px')
        .style('top', event.pageY + 5 + 'px');
    })
    .on('mousemove', (event) => {
      tooltip
        .style('left', event.pageX + 5 + 'px')
        .style('top', event.pageY + 5 + 'px');
    })
    .on('mouseout', () => {
      tooltip.style('opacity', 0);
    });
});

