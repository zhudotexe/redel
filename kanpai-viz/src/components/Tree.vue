<!-- @formatter:off -->
<!-- this file in JS because d3 is wack -->
<script setup>
import {KanpaiClient} from "@/kanpai/client";
import * as d3 from "d3";
import {onMounted, onUnmounted, ref} from "vue";

const props = defineProps({
  client: KanpaiClient
});

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

onMounted(async () => {
  await props.client.waitForReady();

  // Specify the chart’s dimensions.
  const width = 900;
  const height = 400;

  // Compute the graph and start the force simulation.
  const root = d3.hierarchy(
    props.client.rootKani,
    (kani) => kani?.children.map(id => props.client.kaniMap.get(id)),
  );
  const links = root.links();
  const nodes = root.descendants();

  simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(d => d.id).distance(0).strength(1))
      .force("charge", d3.forceManyBody().strength(-50))
      .force("x", d3.forceX())
      .force("y", d3.forceY());

  // Create the container SVG.
  const svg = d3.select(d3Mount.value)
      .attr("viewBox", [-width / 2, -height / 2, width, height])
      .attr("style", "max-width: 100%; height: auto;");

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
      .attr("fill", d => d.children ? null : "#000")
      .attr("stroke", d => d.children ? null : "#fff")
      .attr("r", 3.5)
      .call(drag(simulation));

  node.append("title")
      .text(d => d.data.id);

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
});

onUnmounted(() => simulation.stop());
</script>

<template>
  <svg class="d3" ref="d3Mount"></svg>
</template>

<style scoped>
</style>
