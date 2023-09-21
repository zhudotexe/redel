<!-- @formatter:off -->
<!-- this file in JS because d3 is wack -->
<script setup>
import * as d3 from "d3";
import {inject, onMounted, onUnmounted, ref} from "vue";

const client = inject("client");
const d3Mount = ref(null);
let simulation;

const drag = simulation => {
  function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }

  function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
  }

  function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }

  return d3.drag()
      .on("start", dragstarted)
      .on("drag", dragged)
      .on("end", dragended);
}

// set up the canvas when the page loads
onMounted(async () => {
  await client.waitForReady();

  // Specify the chart’s dimensions.
  const width = 900;
  const height = 400;

  // Create the container SVG.
  const svg = d3.select(d3Mount.value)
      .attr("viewBox", [-width / 2, -height / 2, width, height])
      .attr("style", "max-width: 100%; height: auto;");

  // Compute the graph and start the force simulation.
  const root = d3.hierarchy(
    client.rootKani,
    (kani) => kani?.children.map(id => client.kaniMap.get(id)),
  );
  const links = root.links();
  const nodes = root.descendants();

  simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(d => d.id).distance(0).strength(1))
      .force("charge", d3.forceManyBody().strength(-50))
      .force("x", d3.forceX())
      .force("y", d3.forceY());

  // Append links.
  const link = svg.append("g")
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.6)
    .selectAll("line")
    .data(links)
    .join("line");

  // Append nodes.
  const node = svg.append("g")
      .attr("fill", "#fff")
      .attr("stroke", "#000")
      .attr("stroke-width", 1.5)
    .selectAll("circle")
    .data(nodes)
    .join("circle")
      .attr("id", d => d.data.id)
      .attr("fill", d => d.children ? null : "#000")
      .attr("stroke", d => d.children ? null : "#fff")
      .attr("r", 3.5)
      .call(drag(simulation));

  node.append("title")
      .text(d => d.data.id);

  // simulation: move on each tick
  simulation.on("tick", () => {
    link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

    node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y);
  });

  // flash on click
  node.on("click", function() {
    console.log(this)
    d3.select(this)
      .transition() // starts a transition
      .ease(d3.easeCubic) // controls the timing of the transition
      .duration(1000) // for one second
      .style("fill", "red") // change the color to red
      .transition() // starts a transition
      .ease(d3.easeCubic) // controls the timing of the transition
      .duration(1000) // for one second
      .style("fill", "blue"); // and then change the color back to blue
  });
});

onUnmounted(() => simulation.stop());
</script>

<template>
  <svg class="d3" ref="d3Mount"></svg>
</template>

<style scoped>
</style>
